from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    success: bool = Field(default=True)
    message: str = Field(default="Service is healthy")
