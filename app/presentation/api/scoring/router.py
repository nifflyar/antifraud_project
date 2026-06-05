from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Request
from dishka.integrations.fastapi import FromDishka, inject
from dishka import AsyncContainer
import logging

from app.application.scoring.run_scoring import RunScoringInteractor
from app.application.scoring.get_scoring_status import GetScoringStatusInteractor
from app.application.scoring.process_results import ProcessScoringResultsInteractor
from app.presentation.api.scoring.schemas import (
    ScoringRunRequest,
    ScoringRunResponse,
    ScoringStatusResponse,
)

logger = logging.getLogger(__name__)
scoring_router = APIRouter(prefix="/scoring", tags=["Scoring"])


@scoring_router.post(
    "/run",
    response_model=ScoringRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def run_scoring(
    request: Request,
    data: ScoringRunRequest,
    background_tasks: BackgroundTasks,
    interactor: FromDishka[RunScoringInteractor],
):
    """
    Запуск асинхронного процесса скоринга для загруженного файла.
    Возвращает job_id для отслеживания статуса.
    """
    try:
        # 1. Основной интерактор создает задачу в БД (PENDING)
        job_id = await interactor.execute(data.upload_id)
        
        container: AsyncContainer = request.app.state.dishka_container

        # 2. Функция-обертка для запуска задачи в изолированном scope
        async def run_scoring_task(upload_id: int, jid):
            logger.info(f"Начинается фоновый скоринг (job_id={jid.value})")
            try:
                async with container() as task_container:
                    scoring_interactor = await task_container.get(ProcessScoringResultsInteractor)
                    await scoring_interactor.execute(upload_id=upload_id, job_id=jid)
            except Exception as e:
                logger.exception(f"Критическая ошибка при фоновом скоринге: {e}")

        # 3. Добавляем в BackgroundTasks
        background_tasks.add_task(run_scoring_task, data.upload_id, job_id)

        from datetime import datetime
        return ScoringRunResponse(
            job_id=job_id.value,
            status="pending",
            started_at=datetime.now()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@scoring_router.get(
    "/status/{job_id}",
    response_model=ScoringStatusResponse,
)
@inject
async def get_scoring_status(
    job_id: UUID,
    interactor: FromDishka[GetScoringStatusInteractor],
):
    """
    Получение текущего статуса задачи скоринга.
    """
    job = await interactor.execute(str(job_id))
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Scoring job {job_id} not found"
        )
    
    return ScoringStatusResponse(
        job_id=job.id.value,
        upload_id=job.upload_id.value,
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
    )
