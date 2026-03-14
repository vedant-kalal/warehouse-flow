from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str | None = None


class CategoryOut(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)
