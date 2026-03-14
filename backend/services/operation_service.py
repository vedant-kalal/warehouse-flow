from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Operation, OperationItem, Product, Location, User
from schemas.operation import OperationCreate, OperationOut, OperationItemOut
from utils.enums import OperationType, OperationStatus
from utils.exceptions import raise_404, raise_400, raise_422
from services import inventory_service


async def _generate_reference(db: AsyncSession, op_type: OperationType) -> str:
    """Auto-generate operation reference."""
    # Map operation type to prefix
    prefixes = {
        OperationType.receipt: "RCP",
        OperationType.delivery: "DLV",
        OperationType.transfer: "TRF",
        OperationType.adjustment: "ADJ",
    }
    prefix = prefixes.get(op_type, "OP")

    # Get today's date as YYYYMMDD
    today = datetime.utcnow().strftime("%Y%m%d")

    # Count operations created today with this type
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Operation.id)).where(
            (Operation.type == op_type.value) &
            (Operation.created_at >= today_start)
        )
    )
    today_count = result.scalar() or 0

    # Generate reference: RCP-20240101-0001
    seq = str(today_count + 1).zfill(4)
    return f"{prefix}-{today}-{seq}"


async def create_operation(
    db: AsyncSession,
    data: OperationCreate,
    current_user: User
) -> Operation:
    """Create a new operation (initially in draft status)."""
    # Validate based on operation type
    if data.type == OperationType.receipt:
        if not data.dest_location_id:
            raise_422(detail="receipt type requires dest_location_id")
    elif data.type == OperationType.delivery:
        if not data.source_location_id:
            raise_422(detail="delivery type requires source_location_id")
    elif data.type == OperationType.transfer:
        if not data.source_location_id or not data.dest_location_id:
            raise_422(detail="transfer type requires both source_location_id and dest_location_id")
    elif data.type == OperationType.adjustment:
        if not data.source_location_id:
            raise_422(detail="adjustment type requires source_location_id")

    # Generate reference if not provided
    reference = data.reference or await _generate_reference(db, data.type)

    # Create operation
    new_op = Operation(
        type=data.type.value,
        status=OperationStatus.draft.value,
        reference=reference,
        source_location_id=str(data.source_location_id) if data.source_location_id else None,
        dest_location_id=str(data.dest_location_id) if data.dest_location_id else None,
        created_by=current_user.id
    )

    db.add(new_op)
    await db.flush()  # Get the operation ID

    # Create operation items
    for item_data in data.items:
        op_item = OperationItem(
            operation_id=new_op.id,
            product_id=str(item_data.product_id),
            quantity=item_data.quantity
        )
        db.add(op_item)

    await db.commit()
    await db.refresh(new_op)

    return new_op


async def confirm_operation(db: AsyncSession, operation_id: UUID, current_user: User) -> Operation:
    """Confirm a draft operation (transition to confirmed)."""
    # Fetch operation
    result = await db.execute(
        select(Operation)
        .where(Operation.id == str(operation_id))
        .options(joinedload(Operation.items), joinedload(Operation.creator))
    )
    operation = result.unique().scalar_one_or_none()

    if not operation:
        raise_404(detail="Operation not found")

    # Check status is draft
    if operation.status != OperationStatus.draft.value:
        raise_400(detail=f"Can only confirm operations in draft status, current status: {operation.status}")

    operation.status = OperationStatus.confirmed.value
    await db.commit()
    await db.refresh(operation)

    return operation


async def complete_operation(db: AsyncSession, operation_id: UUID, current_user: User) -> Operation:
    """Complete a confirmed operation and apply stock changes."""
    # Fetch operation with all relationships
    result = await db.execute(
        select(Operation)
        .where(Operation.id == str(operation_id))
        .options(
            joinedload(Operation.items).joinedload(OperationItem.product),
            joinedload(Operation.creator),
            joinedload(Operation.source_location),
            joinedload(Operation.dest_location)
        )
    )
    operation = result.unique().scalar_one_or_none()

    if not operation:
        raise_404(detail="Operation not found")

    # Check status is confirmed
    if operation.status != OperationStatus.confirmed.value:
        raise_400(detail=f"Can only complete operations in confirmed status, current status: {operation.status}")

    # Apply stock changes based on operation type
    op_type = OperationType(operation.type)

    if op_type == OperationType.receipt:
        # Add stock to destination location
        for item in operation.items:
            await inventory_service.add_stock(
                db=db,
                product_id=UUID(item.product_id),
                location_id=UUID(operation.dest_location_id),
                qty=item.quantity
            )

    elif op_type == OperationType.delivery:
        # Remove stock from source location
        for item in operation.items:
            await inventory_service.remove_stock(
                db=db,
                product_id=UUID(item.product_id),
                location_id=UUID(operation.source_location_id),
                qty=item.quantity
            )

    elif op_type == OperationType.transfer:
        # Transfer stock from source to destination
        for item in operation.items:
            await inventory_service.transfer_stock(
                db=db,
                product_id=UUID(item.product_id),
                source_location_id=UUID(operation.source_location_id),
                dest_location_id=UUID(operation.dest_location_id),
                qty=item.quantity
            )

    elif op_type == OperationType.adjustment:
        # Adjust stock to counted quantity
        for item in operation.items:
            await inventory_service.adjust_stock(
                db=db,
                product_id=UUID(item.product_id),
                location_id=UUID(operation.source_location_id),
                counted_qty=item.quantity
            )

    operation.status = OperationStatus.done.value
    await db.commit()
    await db.refresh(operation)

    return operation


async def cancel_operation(db: AsyncSession, operation_id: UUID, current_user: User) -> Operation:
    """Cancel an operation (only allowed if draft or confirmed)."""
    # Fetch operation
    result = await db.execute(
        select(Operation).where(Operation.id == str(operation_id))
    )
    operation = result.scalar_one_or_none()

    if not operation:
        raise_404(detail="Operation not found")

    # Check status - cannot cancel completed operations
    if operation.status == OperationStatus.done.value:
        raise_400(detail="Cannot cancel completed operations")

    operation.status = OperationStatus.cancelled.value
    await db.commit()
    await db.refresh(operation)

    return operation


async def get_history(
    db: AsyncSession,
    op_type: OperationType | None = None,
    date_from = None,
    date_to = None,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[Operation], int]:
    """Get operation history with optional filtering."""
    query = select(Operation).options(
        joinedload(Operation.items).joinedload(OperationItem.product),
        joinedload(Operation.creator)
    )

    if op_type:
        query = query.where(Operation.type == op_type.value)

    if date_from:
        query = query.where(Operation.created_at >= date_from)

    if date_to:
        # Add 1 day to include entire end date
        query = query.where(Operation.created_at <= date_to)

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.all())

    # Sort by created_at DESC and paginate
    query = query.order_by(Operation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    operations = result.unique().scalars().all()

    return operations, total
