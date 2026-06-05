from typing import Any, ClassVar, TypeVar

from sqlalchemy import Dialect, TypeDecorator

from app.domain.common.vo.base import BaseValueObject

VO = TypeVar("VO", bound=BaseValueObject[Any])
Raw = TypeVar("Raw")

type VOTypeClass = Any
type VOTypeRaw = Any


class VOType(TypeDecorator):
    vo_class: ClassVar[type[VOTypeClass]]
    vo_raw: ClassVar[type[VOTypeRaw]]

    _vo_class: ClassVar[type[BaseValueObject[Any]]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls is VOType:
            return

        if not hasattr(cls, "vo_class"):
            raise TypeError(f"{cls.__name__} must define `vo_class`")

        if not hasattr(cls, "vo_raw"):
            raise TypeError(f"{cls.__name__} must define `vo_raw`")

        if not isinstance(cls.vo_raw, type):
            raise TypeError(f"{cls.__name__}.vo_raw must be a type")

        if not hasattr(cls, "impl"):
            raise TypeError(
                f"{cls.__name__} must define SQLAlchemy `impl` (e.g., BIGINT())"
            )

        cls._vo_class = cls.vo_class

    def process_bind_param(
        self,
        value: VOTypeClass | VOTypeRaw | None,
        dialect: Dialect,
    ) -> VOTypeRaw | None:
        if value is None:
            return None
        if isinstance(value, self._vo_class):
            return value.value
        return value

    def process_result_value(
        self,
        value: VOTypeRaw | None,
        dialect: Dialect,
    ) -> VOTypeClass | None:
        if value is None:
            return None
        return self._vo_class(value)
