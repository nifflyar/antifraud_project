import uuid
import logging
from typing import Optional

from fastapi import BackgroundTasks

from app.application.scoring.process_results import ProcessScoringResultsInteractor
from app.application.common.transaction import TransactionManager
from app.domain.scoring.entity import ScoringJob
from app.domain.scoring.repository import IScoringJobRepository
from app.domain.scoring.vo import ScoringJobId
from app.domain.upload.repository import IUploadRepository
from app.domain.upload.vo import UploadId

logger = logging.getLogger(__name__)


class RunScoringInteractor:
    """Интерэктор для ручного запуска скоринга."""

    def __init__(
        self,
        upload_repo: IUploadRepository,
        scoring_job_repo: IScoringJobRepository,
        transaction_manager: TransactionManager,
    ):
        self._upload_repo = upload_repo
        self._scoring_job_repo = scoring_job_repo
        self._tx_manager = transaction_manager

    async def execute(
        self, upload_id: int
    ) -> ScoringJobId:
        uid = UploadId(upload_id)
        
        # 1. Проверяем существование загрузки
        upload = await self._upload_repo.get_by_id(uid)
        if not upload:
            raise ValueError(f"Upload with id {upload_id} not found")

        # 2. Создаем задачу скоринга
        job_id = ScoringJobId(uuid.uuid4())
        job = ScoringJob.create(job_id, uid)
        
        await self._scoring_job_repo.create(job)
        await self._tx_manager.commit()
        
        logger.info(f"Created scoring job {job_id.value} for upload {upload_id}")

        return job_id
