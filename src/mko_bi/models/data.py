from pydantic import BaseModel
from typing import Any, Dict, Optional


class UploadResponse(BaseModel):
    status: str = "ok"

    class Config:
        from_attributes = True


class DataFilter(BaseModel):
    year: Optional[int] = None
    category: Optional[str] = None
    brand: Optional[str] = None

    class Config:
        from_attributes = True


class DataResponse(BaseModel):
    data: list = []

    class Config:
        from_attributes = True
