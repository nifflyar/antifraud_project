import logging
import asyncio
import tempfile
import os
from typing import Annotated
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Request, UploadFile, HTTPException, status, Query, BackgroundTasks
from dishka.integrations.fastapi import FromDishka, inject
from dishka import AsyncContainer

from app.application.upload.create_upload import CreateUploadInputDTO, CreateUploadInteractor
from app.application.upload.get_upload import GetUploadInputDTO, GetUploadInteractor
from app.application.upload.list_uploads import ListUploadsInputDTO, ListUploadsInteractor
from app.application.etl.pipeline import EtlPipeline
from app.application.scoring.process_results import ProcessScoringResultsInteractor
from app.infrastructure.config import Config
from app.presentation.api.security import get_optional_auth_claims_from_request
from app.presentation.api.upload.schemas import UploadListResponse, UploadResponse
from app.presentation.api.upload.websocket import get_progress_manager

logger = logging.getLogger(__name__)
_file_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="file_io_")

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/excel", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
@inject
async def upload_excel(
    request: Request,
    background_tasks: BackgroundTasks,
    config: FromDishka[Config],
    create_upload: FromDishka[CreateUploadInteractor],
    file: UploadFile = File(...),
) -> UploadResponse:
    """Загрузить Excel-файл с транзакциями для ETL-пайплайна."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    filename = file.filename or "unknown.xlsx"
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Только файлы .xlsx поддерживаются"
        )

    # Stream file to disk (don't load entire file into memory)
    temp_dir = tempfile.gettempdir()
    temp_filepath = os.path.join(temp_dir, f"upload_{os.urandom(8).hex()}.xlsx")

    async def save_file_chunks():
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        loop = asyncio.get_event_loop()

        def write_chunk(data):
            with open(temp_filepath, 'ab') as f:
                f.write(data)
            return len(data)

        while chunk := await file.read(chunk_size):
            chunk_len = await loop.run_in_executor(_file_executor, write_chunk, chunk)
            file_size += chunk_len

        return file_size

    try:
        file_size = await save_file_chunks()

        if file_size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пуст")

        logger.info(f"Файл загружен на диск: {temp_filepath} ({file_size / 1024 / 1024:.2f}MB)")

        # 1. Создаем запись о загрузке со статусом PENDING
        upload_dto = await create_upload(
            CreateUploadInputDTO(
                filename=filename,
                filepath=temp_filepath,
                user_id=claims.user_id,
            )
        )

        root_container: AsyncContainer = request.app.state.dishka_container

        # 2. The parser itself offloads XLSX reading to a worker thread, while
        # ETL database work stays on the app event loop.
        async def run_etl_task(upload_id: int, filepath: str, user_id):
            logger.info(f"Начинается фоновая обработка файла (upload_id={upload_id})")
            progress_manager = get_progress_manager()

            try:
                await progress_manager.broadcast_progress(
                    upload_id, {"status": "processing", "message": "Обработка начата"}
                )

                async with root_container() as task_container:
                    etl_pipeline = await task_container.get(EtlPipeline)
                    result = await etl_pipeline.run(upload_id=upload_id, filepath=filepath, user_id=user_id)

                await progress_manager.broadcast_progress(
                    upload_id, {"status": "completed", "message": "Загрузка успешно завершена"}
                )

                if result.success:
                    try:
                        await progress_manager.broadcast_progress(
                            upload_id,
                            {"status": "scoring", "message": "Запущен скоринг рисков"},
                        )
                        async with root_container() as scoring_container:
                            scoring = await scoring_container.get(ProcessScoringResultsInteractor)
                            await scoring.execute(upload_id=upload_id)
                        await progress_manager.broadcast_progress(
                            upload_id,
                            {"status": "scored", "message": "Скоринг завершен"},
                        )
                    except Exception as scoring_error:
                        # Data load is already DONE; scoring failure must not turn a
                        # successful million-row import into FAILED.
                        logger.exception(
                            "Ошибка скоринга после загрузки upload_id=%s: %s",
                            upload_id,
                            scoring_error,
                        )
                        await progress_manager.broadcast_progress(
                            upload_id,
                            {
                                "status": "scoring_error",
                                "message": "Данные загружены, но скоринг не завершился",
                            },
                        )
            except Exception as e:
                logger.exception(f"Критическая ошибка при фоновой обработке файла: {e}")
                await progress_manager.broadcast_progress(
                    upload_id, {"status": "error", "message": str(e)}
                )
            finally:
                # Clean up temp file
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(_file_executor, lambda: os.remove(filepath))
                    logger.info(f"Временный файл удален: {filepath}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {filepath}: {e}")

        # 3. Добавляем задачу в фон
        background_tasks.add_task(
            run_etl_task,
            upload_id=upload_dto.id,
            filepath=temp_filepath,
            user_id=claims.user_id
        )

        return UploadResponse(
            id=str(upload_dto.id),
            filename=upload_dto.filename,
            status=upload_dto.status,
            uploaded_at=str(upload_dto.uploaded_at),
            uploaded_by_user_id=str(claims.user_id.value) if claims.user_id else None,
            error_message=None,
        )
    except Exception as e:
        # Clean up on error
        try:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        except Exception:
            pass
        raise


@router.get("", response_model=UploadListResponse)
@inject
async def list_uploads(
    request: Request,
    config: FromDishka[Config],
    list_interactor: FromDishka[ListUploadsInteractor],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> UploadListResponse:
    """Получить список всех загрузок (с пагинацией)."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await list_interactor(ListUploadsInputDTO(limit=limit, offset=offset))

    # count_all мы пока не реализовали для Upload, 
    # поэтому просто вернем размер текущего батча + offset как заглушку, 
    # либо нужно дописать count в IUploadRepository
    return UploadListResponse(
        items=[
            UploadResponse(
                id=str(item.id),
                filename=item.filename,
                status=item.status,
                uploaded_at=str(item.uploaded_at),
                uploaded_by_user_id=str(item.uploaded_by_user_id) if item.uploaded_by_user_id else None,
                error_message=item.error_message,
            )
            for item in result.items
        ],
        total=len(result.items) + offset, # заглушка для total
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{upload_id}", response_model=UploadResponse)
@inject
async def get_upload(
    upload_id: int,
    request: Request,
    config: FromDishka[Config],
    get_interactor: FromDishka[GetUploadInteractor],
) -> UploadResponse:
    """Получить статус конкретной загрузки."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        result = await get_interactor(GetUploadInputDTO(upload_id=upload_id))
        return UploadResponse(
            id=str(result.id),
            filename=result.filename,
            status=result.status,
            uploaded_at=str(result.uploaded_at),
            uploaded_by_user_id=str(result.uploaded_by_user_id) if result.uploaded_by_user_id else None,
            error_message=getattr(result, "error_message", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

upload_router = router
