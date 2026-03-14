from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    sku: str
    category_id: UUID
    unit: str
    reorder_level: int = 0


class ProductUpdate(BaseModel):
    name: str | None = None
    category_id: UUID | None = None
    unit: str | None = None
    reorder_level: int | None = None


class ProductOut(BaseModel):
    id: UUID
    name: str
    sku: str
    category_id: UUID
    category_name: str | None = None
    unit: str
    reorder_level: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
