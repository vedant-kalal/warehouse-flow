from uuid import uuid4
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("product_id", "location_id"),
    )

    # Relationships
    product = relationship("Product", back_populates="inventory_entries")
    location = relationship("Location", back_populates="inventory_entries")

    @property
    def free_to_use(self) -> int:
        return self.quantity - self.reserved_qty
