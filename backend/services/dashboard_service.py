from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Product, Inventory, Operation, Warehouse
from schemas.dashboard import KPIResponse
from utils.enums import OperationType, OperationStatus


async def get_kpis(db: AsyncSession) -> KPIResponse:
    """Calculate and return dashboard KPIs."""

    # 1. Total products (active only)
    total_products_result = await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True)
    )
    total_products = total_products_result.scalar() or 0

    # 2. Low stock count
    low_stock_result = await db.execute(
        select(func.count(Inventory.id))
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .where((Inventory.quantity < Product.reorder_level) & (Product.is_active == True))
    )
    low_stock_count = low_stock_result.scalar() or 0

    # 3. Pending receipts
    pending_receipts_result = await db.execute(
        select(func.count(Operation.id)).where(
            (Operation.type == OperationType.receipt.value) &
            (Operation.status == OperationStatus.confirmed.value)
        )
    )
    pending_receipts = pending_receipts_result.scalar() or 0

    # 4. Pending deliveries
    pending_deliveries_result = await db.execute(
        select(func.count(Operation.id)).where(
            (Operation.type == OperationType.delivery.value) &
            (Operation.status == OperationStatus.confirmed.value)
        )
    )
    pending_deliveries = pending_deliveries_result.scalar() or 0

    # 5. Total warehouses
    total_warehouses_result = await db.execute(select(func.count(Warehouse.id)))
    total_warehouses = total_warehouses_result.scalar() or 0

    # 6. Out of stock count
    out_of_stock_result = await db.execute(
        select(func.count(Inventory.id)).where(Inventory.quantity == 0)
    )
    out_of_stock_count = out_of_stock_result.scalar() or 0

    return KPIResponse(
        total_products=total_products,
        low_stock_count=low_stock_count,
        pending_receipts=pending_receipts,
        pending_deliveries=pending_deliveries,
        total_warehouses=total_warehouses,
        out_of_stock_count=out_of_stock_count
    )
