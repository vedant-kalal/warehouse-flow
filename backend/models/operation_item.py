from uuid import uuid4

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class OperationItem(Base):
    __tablename__ = "operation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    operation_id: Mapped[str] = mapped_column(String(36), ForeignKey("operations.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    operation = relationship("Operation", back_populates="items")
    product = relationship("Product", back_populates="operation_items")
