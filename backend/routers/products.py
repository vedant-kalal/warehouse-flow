from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.product import ProductCreate, ProductUpdate, ProductOut
from services import product_service
from auth.dependencies import get_current_user, require_role
from models import User
from utils.response import paginated, success

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("", response_model=dict)
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category_id: UUID | None = None,
    is_active: bool = Query(True)
) -> dict:
    """List all products with pagination."""
    products, total = await product_service.get_all(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active
    )

    # Format response
    product_list = []
    for p in products:
        product_list.append(ProductOut(
            id=UUID(p.id),
            name=p.name,
            sku=p.sku,
            category_id=UUID(p.category_id),
            category_name=p.category.name if p.category else None,
            unit=p.unit,
            reorder_level=p.reorder_level,
            is_active=p.is_active,
            created_at=p.created_at
        ))

    return paginated(product_list, total, skip, limit)


@router.get("/{product_id}", response_model=dict)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get a single product by ID."""
    product = await product_service.get_by_id(db, product_id)

    product_out = ProductOut(
        id=UUID(product.id),
        name=product.name,
        sku=product.sku,
        category_id=UUID(product.category_id),
        category_name=product.category.name if product.category else None,
        unit=product.unit,
        reorder_level=product.reorder_level,
        is_active=product.is_active,
        created_at=product.created_at
    )

    return success(product_out)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
) -> dict:
    """Create a new product."""
    product = await product_service.create(db, data)

    product_out = ProductOut(
        id=UUID(product.id),
        name=product.name,
        sku=product.sku,
        category_id=UUID(product.category_id),
        category_name=product.category.name if product.category else None,
        unit=product.unit,
        reorder_level=product.reorder_level,
        is_active=product.is_active,
        created_at=product.created_at
    )

    return success(product_out, message="Product created successfully")


@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
) -> dict:
    """Update a product."""
    product = await product_service.update(db, product_id, data)

    product_out = ProductOut(
        id=UUID(product.id),
        name=product.name,
        sku=product.sku,
        category_id=UUID(product.category_id),
        category_name=product.category.name if product.category else None,
        unit=product.unit,
        reorder_level=product.reorder_level,
        is_active=product.is_active,
        created_at=product.created_at
    )

    return success(product_out, message="Product updated successfully")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
) -> None:
    """Soft delete a product."""
    await product_service.soft_delete(db, product_id)
