from uuid import UUID
from datetime import date
from pydantic import BaseModel, ConfigDict

from utils.enums import OperationType, OperationStatus


class SearchFilters(BaseModel):
    # Product
    product_query: str | None = None
    name: str | None = None
    sku: str | None = None
    category: str | None = None

    # Inventory
    available_only: bool | None = None
    low_stock: bool | None = None
    min_qty: int | None = None
    max_qty: int | None = None

    # Location / Warehouse
    warehouse: str | None = None
    location: str | None = None

    # Operations
    op_type: OperationType | None = None
    op_status: OperationStatus | None = None
    date_from: date | None = None
    date_to: date | None = None

    # Search behaviour
    fetch_all: bool = False
    similarity_threshold: float = 0.75


class SearchResult(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    category: str
    quantity: int
    free_to_use: int
    warehouse: str
    location: str
    similarity: float | None = None
    match_type: str


class SearchResponse(BaseModel):
    query: str
    filters_applied: SearchFilters
    total: int
    results: list[SearchResult]

    model_config = ConfigDict(from_attributes=True)
