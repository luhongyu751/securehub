from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class DocumentOut(BaseModel):
    id: int
    filename: str
    watermark_enabled: bool

    class Config:
        orm_mode = True
