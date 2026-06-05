from dataclasses import dataclass
from datetime import datetime, UTC
import logging

from app.domain.passenger.vo import PassengerId, RiskBand
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.application.services.audit import AuditService
from app.application.common.transaction import TransactionManager
from app.domain.user.vo import UserId

logger = logging.getLogger(__name__)

@dataclass
class OverrideRiskInput:
    passenger_id: int
    new_risk_band: RiskBand
    reason: str
    actor_user_id: UserId

class OverridePassengerRiskInteractor:
    def __init__(
        self,
        score_repo: IPassengerScoreRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
    ):
        self._score_repo = score_repo
        self._audit = audit_service
        self._tx_manager = transaction_manager

    async def execute(self, input_dto: OverrideRiskInput) -> None:
        pid = PassengerId(input_dto.passenger_id)
        
        # 1. Получаем текущий скор
        score = await self._score_repo.get_by_passenger_id(pid)
        
        if not score:
            # Если скора ещё нет, создаем пустой
            from app.domain.passenger.entity import PassengerScore
            score = PassengerScore()
        
        # 2. Обновляем поля
        old_band = score.risk_band
        score.risk_band = input_dto.new_risk_band
        score.is_manual = True
        score.scored_at = datetime.now(UTC)
        
        # Добавляем причину в список причин
        reason_msg = f"MANUAL OVERRIDE: {input_dto.reason}"
        if reason_msg not in score.top_reasons:
            score.top_reasons.insert(0, reason_msg)
        
        # 3. Сохраняем
        await self._score_repo.save(pid, score)
        
        # 4. Логируем аудит
        await self._audit.log_action(
            action="PASSENGER_RISK_OVERRIDE",
            entity_type="passenger",
            entity_id=str(input_dto.passenger_id),
            user_id=input_dto.actor_user_id,
            meta={
                "old_band": old_band.value,
                "new_band": input_dto.new_risk_band.value,
                "reason": input_dto.reason
            }
        )
        
        await self._tx_manager.commit()
        logger.info(f"Manual risk override saved for passenger {input_dto.passenger_id} by user {input_dto.actor_user_id}")
