from pydantic import BaseModel, EmailStr
from typing import Literal


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "editor", "viewer"]

    class Config:
        from_attributes = True


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: Literal["admin", "editor", "viewer"]

    class Config:
        from_attributes = True


class UserDB(BaseModel):
    id: int
    email: EmailStr
    password_hash: str
    role: Literal["admin", "editor", "viewer"]

    class Config:
        from_attributes = True
