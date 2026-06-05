from pydantic import BaseModel, ConfigDict


class BaseRequestDTO(BaseModel):
    """Base request DTO with camelCase field serialization"""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(x.split("_"))
        ),
    )


class BaseResponseDTO(BaseModel):
    """Base response DTO with camelCase field serialization"""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda x: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(x.split("_"))
        ),
    )
