from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

InputDTO = TypeVar("InputDTO")
OutputDTO = TypeVar("OutputDTO")


class Interactor[InputDTO, OutputDTO](ABC):
    @abstractmethod
    async def __call__(self, data: InputDTO) -> OutputDTO:
        """Execute the interactor with the given input data and return the output data."""


InteractorFactory = Callable[[], Interactor[InputDTO, OutputDTO]]
