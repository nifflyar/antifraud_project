from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

from dature.fields.secret_str import SecretStr


@dataclass(frozen=True, slots=True, kw_only=True)
class Url:
    """Validates that a string is a well-formed URL with a scheme and network location."""

    error_message: str = "Value must be a valid URL with scheme and host"

    def get_validator_func(self) -> Callable[[str | SecretStr], bool]:
        def validate(val: str | SecretStr) -> bool:
            raw = val.get_secret_value() if isinstance(val, SecretStr) else val
            try:
                parsed = urlparse(raw)
            except (ValueError, AttributeError):
                return False
            return bool(parsed.scheme and parsed.netloc)

        return validate

    def get_error_message(self) -> str:
        return self.error_message


_HTTP_SCHEMES = frozenset({"http", "https"})


@dataclass(frozen=True, slots=True, kw_only=True)
class HttpUrl:
    """Validates that a string is a well-formed HTTP or HTTPS URL."""

    error_message: str = "Value must be a valid HTTP(S) URL"

    def get_validator_func(self) -> Callable[[str | SecretStr], bool]:
        def validate(val: str | SecretStr) -> bool:
            raw = val.get_secret_value() if isinstance(val, SecretStr) else val
            try:
                parsed = urlparse(raw)
            except (ValueError, AttributeError):
                return False
            return parsed.scheme in _HTTP_SCHEMES and bool(parsed.netloc)

        return validate

    def get_error_message(self) -> str:
        return self.error_message
