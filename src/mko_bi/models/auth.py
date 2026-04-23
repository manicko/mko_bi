from pydantic import BaseModel, EmailStr
from typing import Literal


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True
