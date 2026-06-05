from http import HTTPStatus

from app.application.common.exceptions import ApplicationError, ValidationError


class InvalidAuthDataError(ValidationError): ...


class InvalidRefreshTokenError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
