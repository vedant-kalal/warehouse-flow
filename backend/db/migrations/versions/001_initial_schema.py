"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='staff'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(100), unique=True, nullable=False),
        sa.Column('category_id', sa.String(36), sa.ForeignKey('categories.id'), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('reorder_level', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create warehouses table
    op.create_table(
        'warehouses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('short_code', sa.String(20), unique=True, nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('short_code', sa.String(20), nullable=False),
        sa.Column('warehouse_id', sa.String(36), sa.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('short_code', 'warehouse_id'),
    )

    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False, server_default='0'),
        sa.Column('reserved_qty', sa.Integer, nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('product_id', 'location_id'),
    )

    # Create operations table
    op.create_table(
        'operations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('reference', sa.String(100), unique=True, nullable=False),
        sa.Column('source_location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('dest_location_id', sa.String(36), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create operation_items table
    op.create_table(
        'operation_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('operation_id', sa.String(36), sa.ForeignKey('operations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('operation_items')
    op.drop_table('operations')
    op.drop_table('inventory')
    op.drop_table('locations')
    op.drop_table('warehouses')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')
