from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models import Product, Category


async def search(
    db: AsyncSession,
    keyword: str,
    product_ids: list[UUID] | None = None
) -> list[UUID]:
    """
    Fallback keyword search using ILIKE (PostgreSQL text matching).

    Search for keyword in:
      - products.name
      - products.sku
      - categories.name

    Args:
        db: AsyncSession
        keyword: Search term
        product_ids: Optional list of product IDs to limit search scope

    Returns:
        List of matching product IDs
    """

    # Build ILIKE pattern
    like_pattern = f"%{keyword}%"

    # Build query
    query = select(Product.id).join(Category)

    # Add ILIKE conditions for name, sku, category
    query = query.where(
        or_(
            Product.name.ilike(like_pattern),
            Product.sku.ilike(like_pattern),
            Category.name.ilike(like_pattern)
        )
    )

    # If product IDs provided, limit to subset
    if product_ids:
        query = query.where(Product.id.in_([str(pid) for pid in product_ids]))

    # Execute query
    result = await db.execute(query)
    matched_ids = result.scalars().all()

    return matched_ids
