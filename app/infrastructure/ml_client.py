import httpx
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MlScoringResult:
    passenger_id: int
    rule_score: float
    ml_score: float
    final_score: float
    risk_band: str
    top_reasons: List[str]
    # Признаки
    total_tickets: int
    refund_cnt: int
    refund_share: float
    night_tickets: int
    night_share: float
    max_tickets_month: int = 0
    max_tickets_same_depday: int = 0
    tickets_per_train_peak: float = 0.0
    late_refunds: int = 0
    late_refund_share: float = 0.0
    very_late_refunds: int = 0
    very_late_refund_share: float = 0.0
    quick_refunds: int = 0
    quick_refund_share: float = 0.0
    activity_days: int = 1
    suspicious_refund_pattern_cnt: int = 0
    refund_amount_diversity: float = 1.0
    seat_blocking_flag: bool = False
    refund_close_ratio: float = 0.0
    fake_fio: float = 0.0

class MlServiceClient:
    """Клиент для общения с микросервисом ML-скоринга."""

    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def run_scoring(self, upload_id: int) -> List[MlScoringResult]:
        """Запрашивает скоринг для указанного upload_id.
        
        Возвращает список результатов для каждого пассажира.
        """
        url = f"{self.base_url}/score"
        payload = {"upload_id": upload_id}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Calling ML service at {url} for upload_id={upload_id}")
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                if data.get("status") in {"success", "done"}:
                    results = data.get("results", [])
                    return [MlScoringResult(**r) for r in results]
                
                logger.warning(f"ML service returned non-success status: {data.get('status')}")
                return []

            except httpx.HTTPStatusError as e:
                logger.error(f"ML service error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error calling ML service: {e}")
                raise
