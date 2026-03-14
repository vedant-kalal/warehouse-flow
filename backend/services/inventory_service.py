from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Inventory, Product, Location, Warehouse
from utils.exceptions import raise_404, raise_insufficient_stock


async def get_stock(
    db: AsyncSession,
    warehouse_id: UUID | None = None,
    location_id: UUID | None = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[dict], int]:
    """Get stock levels with optional filtering."""
    query = select(Inventory).options(
        joinedload(Inventory.product),
        joinedload(Inventory.location).joinedload(Location.warehouse)
    )

    if location_id:
        query = query.where(Inventory.location_id == str(location_id))

    if warehouse_id:
        query = query.join(Location).where(Location.warehouse_id == str(warehouse_id))

    if low_stock_only:
        query = query.join(Product).where(Inventory.quantity < Product.reorder_level)

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.all())

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    inventory_items = result.unique().scalars().all()

    # Format response
    formatted_results = []
    for inv in inventory_items:
        formatted_results.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "product_name": inv.product.name,
            "sku": inv.product.sku,
            "location_id": inv.location_id,
            "location_name": inv.location.name,
            "warehouse_name": inv.location.warehouse.name,
            "quantity": inv.quantity,
            "reserved_qty": inv.reserved_qty,
            "free_to_use": inv.free_to_use,
            "updated_at": inv.updated_at,
        })

    return formatted_results, total


async def get_low_stock(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[dict], int]:
    """Get low stock items (quantity < reorder_level)."""
    return await get_stock(
        db=db,
        low_stock_only=True,
        skip=skip,
        limit=limit
    )


async def add_stock(
    db: AsyncSession,
    product_id: UUID,
    location_id: UUID,
    qty: int
) -> Inventory:
    """Add stock to inventory (upsert pattern)."""
    # Try to find existing inventory
    result = await db.execute(
        select(Inventory).where(
            (Inventory.product_id == str(product_id)) &
            (Inventory.location_id == str(location_id))
        )
    )
    inventory = result.scalar_one_or_none()

    if inventory:
        # Update existing
        inventory.quantity += qty
    else:
        # Create new
        inventory = Inventory(
            product_id=str(product_id),
            location_id=str(location_id),
            quantity=qty
        )
        db.add(inventory)

    await db.commit()
    await db.refresh(inventory)
    return inventory


async def remove_stock(
    db: AsyncSession,
    product_id: UUID,
    location_id: UUID,
    qty: int
) -> Inventory:
    """Remove stock from inventory."""
    # Fetch inventory
    result = await db.execute(
        select(Inventory).where(
            (Inventory.product_id == str(product_id)) &
            (Inventory.location_id == str(location_id))
        )
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise_404(detail="Inventory record not found")

    # Check if enough free stock exists
    free_to_use = inventory.quantity - inventory.reserved_qty
    if free_to_use < qty:
        raise_insufficient_stock(available=free_to_use, requested=qty)

    inventory.quantity -= qty
    await db.commit()
    await db.refresh(inventory)
    return inventory


async def transfer_stock(
    db: AsyncSession,
    product_id: UUID,
    source_location_id: UUID,
    dest_location_id: UUID,
    qty: int
) -> tuple[Inventory, Inventory]:
    """Transfer stock from one location to another (atomic)."""
    # Remove from source
    source_inv = await remove_stock(db, product_id, source_location_id, qty)

    # Add to destination
    dest_inv = await add_stock(db, product_id, dest_location_id, qty)

    return source_inv, dest_inv


async def adjust_stock(
    db: AsyncSession,
    product_id: UUID,
    location_id: UUID,
    counted_qty: int
) -> dict:
    """Adjust stock based on physical count."""
    # Fetch inventory
    result = await db.execute(
        select(Inventory).where(
            (Inventory.product_id == str(product_id)) &
            (Inventory.location_id == str(location_id))
        )
    )
    inventory = result.scalar_one_or_none()

    if not inventory:
        raise_404(detail="Inventory record not found")

    current = inventory.quantity
    delta = counted_qty - current
    inventory.quantity = counted_qty

    await db.commit()

    return {
        "previous": current,
        "counted": counted_qty,
        "delta": delta
    }
