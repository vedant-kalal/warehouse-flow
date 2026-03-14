from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from utils.enums import OperationType, OperationStatus


class OperationItemCreate(BaseModel):
    product_id: UUID
    quantity: int

    def __init__(self, **data):
        super().__init__(**data)
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")


class OperationItemOut(BaseModel):
    id: UUID
    operation_id: UUID
    product_id: UUID
    quantity: int
    product_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OperationCreate(BaseModel):
    type: OperationType
    reference: str | None = None
    source_location_id: UUID | None = None
    dest_location_id: UUID | None = None
    items: list[OperationItemCreate]

    def __init__(self, **data):
        super().__init__(**data)
        if not self.items or len(self.items) == 0:
            raise ValueError("At least one item is required")


class OperationOut(BaseModel):
    id: UUID
    type: OperationType
    status: OperationStatus
    reference: str
    source_location_id: UUID | None = None
    dest_location_id: UUID | None = None
    created_by: UUID
    creator_email: str | None = None
    created_at: datetime
    items: list[OperationItemOut] = []

    model_config = ConfigDict(from_attributes=True)
