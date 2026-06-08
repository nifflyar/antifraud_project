from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    is_admin: bool = False
    role: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class SuccessResponse(BaseModel):
    success: bool
