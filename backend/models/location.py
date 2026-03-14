from uuid import uuid4

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_code: Mapped[str] = mapped_column(String(20), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("short_code", "warehouse_id"),
    )

    # Relationships
    warehouse = relationship("Warehouse", back_populates="locations")
    inventory_entries = relationship("Inventory", back_populates="location")
    source_operations = relationship(
        "Operation",
        back_populates="source_location",
        foreign_keys="Operation.source_location_id"
    )
    dest_operations = relationship(
        "Operation",
        back_populates="dest_location",
        foreign_keys="Operation.dest_location_id"
    )
