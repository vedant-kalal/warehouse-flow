from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_products: int
    low_stock_count: int
    pending_receipts: int
    pending_deliveries: int
    total_warehouses: int
    out_of_stock_count: int
