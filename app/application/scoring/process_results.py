from dataclasses import dataclass
from datetime import datetime, UTC
import logging

from app.domain.passenger.entity import PassengerFeatures, PassengerScore
from app.domain.passenger.feature_repository import IPassengerFeatureRepository
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.domain.passenger.vo import PassengerId, RiskBand
from app.domain.scoring.repository import IScoringJobRepository
from app.domain.scoring.vo import ScoringJobId
from app.infrastructure.ml_client import MlServiceClient, MlScoringResult
from app.application.common.transaction import TransactionManager
from app.domain.transaction.repository import ITransactionRepository
from app.domain.risk.repository import IRiskConcentrationRepository

logger = logging.getLogger(__name__)

def _normalize_top_reasons(raw_reasons: list | None) -> list[str]:
    reasons: list[str] = []
    for reason in raw_reasons or []:
        if isinstance(reason, str):
            reasons.append(reason)
            continue
        if isinstance(reason, dict):
            text = reason.get("text") or reason.get("code")
            if text:
                reasons.append(str(text))
            continue
        if reason is not None:
            reasons.append(str(reason))
    return reasons

class ProcessScoringResultsInteractor:
    """Интерэктор для запуска ML-скоринга и обработки результатов.
    
    1. Вызывает ML-микросервис
    2. Сохраняет признаки в passenger_features
    3. Сохраняет результаты скоринга в passenger_scores
    """
    
    def __init__(
        self,
        ml_client: MlServiceClient,
        feature_repo: IPassengerFeatureRepository,
        score_repo: IPassengerScoreRepository,
        scoring_job_repo: IScoringJobRepository,
        transaction_repo: ITransactionRepository,
        risk_repo: IRiskConcentrationRepository,
        transaction_manager: TransactionManager,
    ):
        self._ml_client = ml_client
        self._feature_repo = feature_repo
        self._score_repo = score_repo
        self._scoring_job_repo = scoring_job_repo
        self._tx_repo = transaction_repo
        self._risk_repo = risk_repo
        self._tx_manager = transaction_manager

    async def execute(self, upload_id: int, job_id: ScoringJobId | None = None) -> None:
        logger.info(f"Processing scoring results for upload_id={upload_id}, job_id={job_id}")
        
        job = None
        if job_id:
            job = await self._scoring_job_repo.get_by_id(job_id)
            if job:
                job.mark_running()
                await self._scoring_job_repo.update(job)
                await self._tx_manager.commit()

        try:
            # 1. Получаем результаты от ML-сервиса
            ml_results: list[MlScoringResult] = await self._ml_client.run_scoring(upload_id)
            if not ml_results:
                logger.warning(f"No scoring results returned for upload_id={upload_id}")
                return

            features_to_save = []
            scores_to_save = []
            now = datetime.now(UTC)

            # 2. Мапим результаты в доменные модели
            for res in ml_results:
                pid = PassengerId(res.passenger_id)

                # Признаки - сохраняем ВСЕ поля из ML результатов
                features = PassengerFeatures(
                    total_tickets=res.total_tickets,
                    refund_cnt=res.refund_cnt,
                    refund_share=res.refund_share,
                    night_tickets=res.night_tickets,
                    night_share=res.night_share,
                    max_tickets_month=res.max_tickets_month,
                    max_tickets_same_depday=res.max_tickets_same_depday,
                    refund_close_ratio=res.refund_close_ratio,
                    tickets_per_train_peak=res.tickets_per_train_peak,
                    fio_fake_score_max=res.fake_fio,
                    late_refunds=getattr(res, 'late_refunds', 0),
                    late_refund_share=getattr(res, 'late_refund_share', 0.0),
                    very_late_refunds=getattr(res, 'very_late_refunds', 0),
                    very_late_refund_share=getattr(res, 'very_late_refund_share', 0.0),
                    quick_refunds=getattr(res, 'quick_refunds', 0),
                    quick_refund_share=getattr(res, 'quick_refund_share', 0.0),
                    activity_days=getattr(res, 'activity_days', 1),
                    suspicious_refund_pattern_cnt=getattr(res, 'suspicious_refund_pattern_cnt', 0),
                    refund_amount_diversity=getattr(res, 'refund_amount_diversity', 1.0),
                    seat_blocking_flag=getattr(res, 'seat_blocking_flag', False),
                )
                features_to_save.append((pid, features))
                
                # Скоринг
                score = PassengerScore(
                    rule_score=res.rule_score,
                    ml_score=res.ml_score,
                    final_score=res.final_score,
                    risk_band=RiskBand(res.risk_band.lower()),
                    top_reasons=_normalize_top_reasons(res.top_reasons),
                    seat_blocking_flag=getattr(res, "seat_blocking_flag", False),
                    scored_at=now
                )
                scores_to_save.append((pid, score))

            # 3. Сохраняем батчами
            await self._feature_repo.bulk_upsert(features_to_save)
            await self._score_repo.bulk_upsert(scores_to_save)
            
            # 4. РАСЧЕТ КОНЦЕНТРАЦИЙ РРИСКОВ
            logger.info("Recalculating risk concentrations...")
            await self._recalculate_concentrations()
            
            if job:
                job.mark_done()
                await self._scoring_job_repo.update(job)
            
            await self._tx_manager.commit()
            logger.info(f"Successfully processed and saved scoring and concentrations for {len(ml_results)} passengers")

        except Exception as e:
            logger.error(f"Failed to process scoring results: {e}")
            await self._tx_manager.rollback()
            if job:
                try:
                    job.mark_failed(str(e))
                    await self._scoring_job_repo.update(job)
                    await self._tx_manager.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update job status to FAILED: {update_error}")
            raise

    async def _recalculate_concentrations(self) -> None:
        """Пересчитывает концентрацию рисков по всем измерениям."""
        from app.domain.risk.vo import DimensionType
        from app.domain.risk.entity import RiskConcentration
        import hashlib, struct
        
        # Получаем базовую долю подозрительных операций в системе
        total_all = await self._tx_repo.count_all()
        suspicious_all = await self._tx_repo.count_suspicious()
        base_share = suspicious_all / total_all if total_all > 0 else 0.0
        
        dimensions = [
            DimensionType.CHANNEL,
            DimensionType.AGGREGATOR,
            DimensionType.TERMINAL,
            DimensionType.CASHDESK
        ]
        
        concentrations_to_save = []
        
        for dtype in dimensions:
            # Получаем статистику по колонке
            stats = await self._tx_repo.get_dimension_stats(dtype.value)
            
            for row in stats:
                val = str(row["value"])
                # Генерируем ID: hash(type + value)
                id_str = f"{dtype.value}:{val}"
                id_int = struct.unpack(">Q", hashlib.sha256(id_str.encode()).digest()[:8])[0] & 0x7FFFFFFFFFFFFFFF
                
                item = RiskConcentration.create(
                    concentration_id=id_int,
                    dimension_type=dtype,
                    dimension_value=val,
                    total_ops=row["total_count"],
                    highrisk_ops=row["suspicious_count"],
                    base_share=base_share
                )
                concentrations_to_save.append(item)
        
        if concentrations_to_save:
            await self._risk_repo.save_batch(concentrations_to_save)
            logger.info(f"Saved {len(concentrations_to_save)} risk concentration hotspots")
