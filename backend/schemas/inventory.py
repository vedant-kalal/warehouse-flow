from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_computed_from


class InventoryOut(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str | None = None
    sku: str | None = None
    location_id: UUID
    location_name: str | None = None
    warehouse_name: str | None = None
    quantity: int
    reserved_qty: int
    updated_at: datetime

    @property
    def free_to_use(self) -> int:
        return self.quantity - self.reserved_qty

    model_config = ConfigDict(from_attributes=True)
