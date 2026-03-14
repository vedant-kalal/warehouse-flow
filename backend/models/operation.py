from uuid import uuid4
from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    source_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    dest_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="operations", foreign_keys=[created_by])
    items = relationship("OperationItem", back_populates="operation", cascade="all, delete-orphan")
    source_location = relationship(
        "Location",
        back_populates="source_operations",
        foreign_keys=[source_location_id]
    )
    dest_location = relationship(
        "Location",
        back_populates="dest_operations",
        foreign_keys=[dest_location_id]
    )
