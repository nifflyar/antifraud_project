from http import HTTPStatus
from pydantic import BaseModel

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.common.exceptions import ApplicationError, ValidationError
from app.presentation.api.base.schemas import BaseResponseDTO



class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class ValidationErrorResponse(BaseModel):
    detail: str
    status_code: int
    errors: list[FieldError]


def _request_context(request: Request) -> dict[str, str]:
    return {
        "request_method": request.method,
        "request_path": request.url.path,
        "request_query": str(request.url.query) if request.url.query else "",
    }


async def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    return JSONResponse(
        content=ErrorResponse(
            detail="Internal Server Error",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ).model_dump(by_alias=True),
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors"""
    return JSONResponse(
        content=ErrorResponse(
            detail=exc.message,
            status_code=exc.status_code
        ).model_dump(by_alias=True),
        status_code=exc.status_code,
    )


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle application errors"""
    return JSONResponse(
        content=ErrorResponse(
            detail=exc.message,
            status_code=exc.status_code
        ).model_dump(by_alias=True),
        status_code=exc.status_code,
    )


async def value_error_handler(request: Request, exc: ValueError | TypeError) -> JSONResponse:
    """Handle value and type errors"""
    return JSONResponse(
        content=ErrorResponse(
            detail=str(exc),
            status_code=HTTPStatus.BAD_REQUEST
        ).model_dump(by_alias=True),
        status_code=HTTPStatus.BAD_REQUEST,
    )
