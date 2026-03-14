from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Product, Category
from schemas.product import ProductCreate, ProductUpdate, ProductOut
from utils.exceptions import raise_404, raise_409


async def get_all(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    category_id: UUID | None = None,
    is_active: bool = True
) -> tuple[list[Product], int]:
    """Get all products with optional filtering."""
    query = select(Product).where(Product.is_active == is_active)

    if category_id:
        query = query.where(Product.category_id == str(category_id))

    # Get total count
    count_result = await db.execute(select(Product).where(Product.is_active == is_active))
    total = len(count_result.all())

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query.options(joinedload(Product.category)))
    products = result.unique().scalars().all()

    return products, total


async def get_by_id(db: AsyncSession, product_id: UUID) -> Product:
    """Get a product by ID."""
    result = await db.execute(
        select(Product)
        .where(Product.id == str(product_id))
        .options(joinedload(Product.category))
    )
    product = result.unique().scalar_one_or_none()

    if not product:
        raise_404(detail="Product not found")

    return product


async def create(db: AsyncSession, data: ProductCreate) -> Product:
    """Create a new product."""
    # Check if SKU is unique
    result = await db.execute(select(Product).where(Product.sku == data.sku))
    if result.scalar_one_or_none():
        raise_409(detail="SKU already exists")

    # Check if category exists
    result = await db.execute(select(Category).where(Category.id == str(data.category_id)))
    if not result.scalar_one_or_none():
        raise_404(detail="Category not found")

    # Create new product
    new_product = Product(
        name=data.name,
        sku=data.sku,
        category_id=str(data.category_id),
        unit=data.unit,
        reorder_level=data.reorder_level
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # TODO: In production, trigger embedding_service.generate_and_store(new_product) in background

    return new_product


async def update(db: AsyncSession, product_id: UUID, data: ProductUpdate) -> Product:
    """Update a product."""
    product = await get_by_id(db, product_id)

    # Update fields
    if data.name is not None:
        product.name = data.name
    if data.category_id is not None:
        # Verify category exists
        result = await db.execute(select(Category).where(Category.id == str(data.category_id)))
        if not result.scalar_one_or_none():
            raise_404(detail="Category not found")
        product.category_id = str(data.category_id)
    if data.unit is not None:
        product.unit = data.unit
    if data.reorder_level is not None:
        product.reorder_level = data.reorder_level

    await db.commit()
    await db.refresh(product)

    # TODO: If name/category changed, re-trigger embedding generation

    return product


async def soft_delete(db: AsyncSession, product_id: UUID) -> bool:
    """Soft delete a product (set is_active=False)."""
    product = await get_by_id(db, product_id)

    product.is_active = False
    await db.commit()

    return True
