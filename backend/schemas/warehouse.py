from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WarehouseCreate(BaseModel):
    name: str
    short_code: str
    address: str | None = None


class WarehouseUpdate(BaseModel):
    name: str | None = None
    short_code: str | None = None
    address: str | None = None


class WarehouseOut(BaseModel):
    id: UUID
    name: str
    short_code: str
    address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
