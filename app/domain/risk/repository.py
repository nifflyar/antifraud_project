from abc import ABC, abstractmethod
from .entity import RiskConcentration
from app.domain.risk.vo import DimensionType

class IRiskConcentrationRepository(ABC):

    @abstractmethod
    async def get_all_by_dimension(
        self, dimension_type: DimensionType
    ) -> list[RiskConcentration]: ...

    @abstractmethod
    async def get_top_dimension(
        self, dimension_type: str, top_n: int = 1
    ) -> RiskConcentration | None: ...

    @abstractmethod
    async def save_batch(self, items: list[RiskConcentration]) -> None: ...