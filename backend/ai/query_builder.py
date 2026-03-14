from typing import Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, func, text, column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Product, Category, Inventory, Location, Warehouse, Operation, OperationItem, User
from schemas.search import SearchFilters


def build_inventory_query(filters: SearchFilters, product_ids: Optional[list[UUID]] = None):
    """
    Build master inventory query with dynamic NULL-safe filters.

    Returns only active products (is_active=True).
    Automatically computes free_to_use = quantity - reserved_qty.
    """

    # Base query with proper joins
    query = (
        select(
            Inventory.id,
            Inventory.quantity,
            Inventory.reserved_qty,
            (Inventory.quantity - Inventory.reserved_qty).label("free_to_use"),
            Inventory.updated_at,
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.sku,
            Product.unit,
            Product.reorder_level,
            Category.name.label("category_name"),
            Location.id.label("location_id"),
            Location.name.label("location_name"),
            Location.short_code.label("location_code"),
            Warehouse.id.label("warehouse_id"),
            Warehouse.name.label("warehouse_name"),
            Warehouse.short_code.label("warehouse_code"),
        )
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .join(Category, Category.id == Product.category_id)
        .join(Location, Location.id == Inventory.location_id)
        .join(Warehouse, Warehouse.id == Location.warehouse_id)
    )

    # WHERE clause conditions (all NULL-safe)
    conditions = [Product.is_active == True]

    # Product name filter
    if filters.product_name:
        conditions.append(Product.name.ilike(f"%{filters.product_name}%"))

    # SKU filter
    if filters.sku:
        conditions.append(Product.sku == filters.sku)

    # Category filter
    if filters.category:
        conditions.append(Category.name.ilike(f"%{filters.category}%"))

    # Unit filter
    if filters.unit:
        conditions.append(func.lower(Product.unit) == filters.unit.lower())

    # Warehouse name filter
    if filters.warehouse:
        conditions.append(Warehouse.name.ilike(f"%{filters.warehouse}%"))

    # Warehouse code filter
    if filters.warehouse_code:
        conditions.append(func.upper(Warehouse.short_code) == filters.warehouse_code.upper())

    # Location name filter
    if filters.location:
        conditions.append(Location.name.ilike(f"%{filters.location}%"))

    # Location code filter
    if filters.location_code:
        conditions.append(func.upper(Location.short_code) == filters.location_code.upper())

    # Available only (quantity > 0)
    if filters.available_only is True:
        conditions.append(Inventory.quantity > 0)

    # Out of stock (quantity = 0)
    if filters.out_of_stock is True:
        conditions.append(Inventory.quantity == 0)

    # Low stock (quantity < reorder_level)
    if filters.low_stock is True:
        conditions.append(Inventory.quantity < Product.reorder_level)

    # Min quantity
    if filters.min_qty is not None:
        conditions.append(Inventory.quantity >= filters.min_qty)

    # Max quantity
    if filters.max_qty is not None:
        conditions.append(Inventory.quantity <= filters.max_qty)

    # Min free_to_use
    if filters.min_free_to_use is not None:
        conditions.append((Inventory.quantity - Inventory.reserved_qty) >= filters.min_free_to_use)

    # Has reserved stock
    if filters.has_reserved is True:
        conditions.append(Inventory.reserved_qty > 0)

    # Pre-filtered product IDs (from vector search)
    if product_ids:
        conditions.append(Product.id.in_([str(pid) for pid in product_ids]))

    # Apply all conditions
    query = query.where(and_(*conditions))

    # ORDER BY
    if filters.sort_by == "quantity_asc":
        query = query.order_by(Inventory.quantity.asc())
    elif filters.sort_by == "quantity_desc":
        query = query.order_by(Inventory.quantity.desc())
    elif filters.sort_by == "name_asc":
        query = query.order_by(Product.name.asc())
    elif filters.sort_by == "date_desc":
        query = query.order_by(Inventory.updated_at.desc())
    elif filters.sort_by == "date_asc":
        query = query.order_by(Inventory.updated_at.asc())
    else:
        # Default: lowest stock first (most urgent)
        query = query.order_by(Inventory.quantity.asc())

    # LIMIT and OFFSET
    query = query.limit(filters.limit).offset(0)

    return query


def build_operations_query(filters: SearchFilters, product_ids: Optional[list[UUID]] = None):
    """
    Build master operations query with dynamic filters.

    Returns operations with aggregated items summary.
    Supports filtering by type, status, date range, warehouse, location, product.
    """

    # Base query
    query = (
        select(
            Operation.id,
            Operation.type,
            Operation.status,
            Operation.reference,
            Operation.created_at,
            Operation.updated_at,
            User.email.label("created_by_email"),
            (Location.name).label("source_location_name"),
            (Warehouse.name).label("source_warehouse_name"),
        )
        .select_from(Operation)
        .outerjoin(User, User.id == Operation.created_by)
        .outerjoin(Location, Location.id == Operation.source_location_id)
        .outerjoin(Warehouse, Warehouse.id == Location.warehouse_id)
    )

    # WHERE clause conditions
    conditions = []

    # Operation type filter
    if filters.op_type:
        conditions.append(Operation.type == filters.op_type.value)

    # Operation status filter
    if filters.op_status:
        conditions.append(Operation.status == filters.op_status.value)

    # Operation reference filter
    if filters.op_reference:
        conditions.append(Operation.reference.ilike(f"%{filters.op_reference}%"))

    # Date range: from
    if filters.date_from:
        conditions.append(Operation.created_at >= filters.date_from)

    # Date range: to (end of day)
    if filters.date_to:
        from datetime import datetime, timedelta
        end_of_day = filters.date_to + timedelta(days=1)
        conditions.append(Operation.created_at < end_of_day)

    # Warehouse filter (matches either source or dest warehouse)
    # For simplified query, we just match source warehouse
    # In full implementation, would check both via separate JOINs
    if filters.warehouse:
        conditions.append(Warehouse.name.ilike(f"%{filters.warehouse}%"))

    # Location filter
    if filters.location:
        conditions.append(Location.name.ilike(f"%{filters.location}%"))

    # Apply conditions
    if conditions:
        query = query.where(and_(*conditions))

    # ORDER BY
    if filters.sort_by == "date_desc":
        query = query.order_by(Operation.created_at.desc())
    elif filters.sort_by == "date_asc":
        query = query.order_by(Operation.created_at.asc())
    else:
        query = query.order_by(Operation.created_at.desc())

    # LIMIT
    query = query.limit(filters.limit).offset(0)

    return query


def build_products_query(filters: SearchFilters, product_ids: Optional[list[UUID]] = None):
    """
    Build product search query with category joins.
    """

    query = (
        select(
            Product.id,
            Product.name,
            Product.sku,
            Product.category_id,
            Product.unit,
            Product.reorder_level,
            Product.is_active,
            Product.created_at,
            Category.name.label("category_name"),
        )
        .select_from(Product)
        .join(Category, Category.id == Product.category_id)
    )

    conditions = [Product.is_active == True]

    # Product name filter
    if filters.product_name:
        conditions.append(Product.name.ilike(f"%{filters.product_name}%"))

    # SKU filter
    if filters.sku:
        conditions.append(Product.sku == filters.sku)

    # Category filter
    if filters.category:
        conditions.append(Category.name.ilike(f"%{filters.category}%"))

    # Pre-filtered product IDs (from vector search)
    if product_ids:
        conditions.append(Product.id.in_([str(pid) for pid in product_ids]))

    query = query.where(and_(*conditions))
    query = query.limit(filters.limit).offset(0)

    return query


def build_warehouses_query(filters: SearchFilters):
    """
    Build warehouses query with stock aggregates.
    """

    query = (
        select(
            Warehouse.id,
            Warehouse.name,
            Warehouse.short_code,
            Warehouse.address,
            Warehouse.created_at,
        )
        .select_from(Warehouse)
    )

    conditions = []

    if filters.warehouse:
        conditions.append(Warehouse.name.ilike(f"%{filters.warehouse}%"))

    if filters.warehouse_code:
        conditions.append(func.upper(Warehouse.short_code) == filters.warehouse_code.upper())

    if conditions:
        query = query.where(and_(*conditions))

    query = query.limit(filters.limit).offset(0)

    return query


def build_locations_query(filters: SearchFilters, warehouse_id: Optional[UUID] = None):
    """
    Build locations query for a warehouse.
    """

    query = (
        select(
            Location.id,
            Location.name,
            Location.short_code,
            Location.warehouse_id,
            Warehouse.name.label("warehouse_name"),
        )
        .select_from(Location)
        .join(Warehouse, Warehouse.id == Location.warehouse_id)
    )

    conditions = []

    if filters.location:
        conditions.append(Location.name.ilike(f"%{filters.location}%"))

    if filters.location_code:
        conditions.append(func.upper(Location.short_code) == filters.location_code.upper())

    if warehouse_id:
        conditions.append(Location.warehouse_id == str(warehouse_id))

    if conditions:
        query = query.where(and_(*conditions))

    query = query.limit(filters.limit).offset(0)

    return query
