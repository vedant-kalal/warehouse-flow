from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LocationCreate(BaseModel):
    name: str
    short_code: str


class LocationUpdate(BaseModel):
    name: str | None = None
    short_code: str | None = None


class LocationOut(BaseModel):
    id: UUID
    name: str
    short_code: str
    warehouse_id: UUID

    model_config = ConfigDict(from_attributes=True)
