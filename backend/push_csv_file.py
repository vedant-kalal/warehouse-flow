"""
Database Data Loading Script

This script loads CSV files from the data folder into PostgreSQL database tables.
It handles table creation, data type conversion, and proper insertion order with foreign key constraints.

Usage:
    python push_csv_file.py

Environment:
    DATABASE_URL: PostgreSQL connection string (from .env)
    CSV_DATA_PATH: Path to data folder containing CSV files
"""

import asyncio
import csv
import os
from pathlib import Path
from datetime import datetime
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from db.base import Base
from models import (
    Category, Product, Warehouse, Location,
    Inventory, Operation, OperationItem, User
)


# Path to CSV data folder
CSV_DATA_PATH = Path(__file__).parent.parent / "data"


async def create_tables(engine):
    """Create all tables using SQLAlchemy models."""
    print("🔧 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully!")


async def load_categories(db: AsyncSession, csv_path: Path):
    """Load categories from CSV."""
    print("\n📥 Loading categories...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        category = Category(
            id=row['id'],
            name=row['name']
        )
        db.add(category)

    await db.commit()
    print(f"✅ Loaded {len(df)} categories")


async def load_products(db: AsyncSession, csv_path: Path):
    """Load products from CSV."""
    print("\n📥 Loading products...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        # embedding column is empty in CSV, so we skip it (will be generated on demand)
        product = Product(
            id=row['id'],
            name=row['name'],
            sku=row['sku'],
            category_id=row['category_id'],
            unit=row['unit'],
            reorder_level=int(row['reorder_level']),
            is_active=bool(row['is_active']) if isinstance(row['is_active'], bool) else str(row['is_active']).lower() == 'true',
            embedding=None,  # Will be generated later
            created_at=datetime.fromisoformat(str(row['created_at']))
        )
        db.add(product)

    await db.commit()
    print(f"✅ Loaded {len(df)} products")


async def load_warehouses(db: AsyncSession, csv_path: Path):
    """Load warehouses from CSV."""
    print("\n📥 Loading warehouses...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        warehouse = Warehouse(
            id=row['id'],
            name=row['name'],
            short_code=row['short_code'],
            address=row['address'] if pd.notna(row['address']) else None,
            created_at=datetime.fromisoformat(str(row['created_at']))
        )
        db.add(warehouse)

    await db.commit()
    print(f"✅ Loaded {len(df)} warehouses")


async def load_locations(db: AsyncSession, csv_path: Path):
    """Load locations from CSV."""
    print("\n📥 Loading locations...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        location = Location(
            id=row['id'],
            name=row['name'],
            short_code=row['short_code'],
            warehouse_id=row['warehouse_id']
        )
        db.add(location)

    await db.commit()
    print(f"✅ Loaded {len(df)} locations")


async def load_inventory(db: AsyncSession, csv_path: Path):
    """Load inventory from CSV."""
    print("\n📥 Loading inventory...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        inventory = Inventory(
            id=row['id'],
            product_id=row['product_id'],
            location_id=row['location_id'],
            quantity=int(row['quantity']),
            reserved_qty=int(row['reserved_qty']),
            updated_at=datetime.fromisoformat(str(row['updated_at']))
        )
        db.add(inventory)

    await db.commit()
    print(f"✅ Loaded {len(df)} inventory records")


async def load_operations(db: AsyncSession, csv_path: Path):
    """Load operations from CSV."""
    print("\n📥 Loading operations...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        operation = Operation(
            id=row['id'],
            type=row['type'],
            status=row['status'],
            reference=row['reference'],
            source_location_id=row['source_location_id'] if pd.notna(row['source_location_id']) and str(row['source_location_id']).strip() != '00000000-0000-0000-0000-000000000000' else None,
            dest_location_id=row['dest_location_id'] if pd.notna(row['dest_location_id']) and str(row['dest_location_id']).strip() != '00000000-0000-0000-0000-000000000000' else None,
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(str(row['created_at'])),
            updated_at=datetime.fromisoformat(str(row['updated_at']))
        )
        db.add(operation)

    await db.commit()
    print(f"✅ Loaded {len(df)} operations")


async def load_operation_items(db: AsyncSession, csv_path: Path):
    """Load operation items from CSV."""
    print("\n📥 Loading operation items...")
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        operation_item = OperationItem(
            id=row['id'],
            operation_id=row['operation_id'],
            product_id=row['product_id'],
            quantity=int(row['quantity'])
        )
        db.add(operation_item)

    await db.commit()
    print(f"✅ Loaded {len(df)} operation items")



async def main():
    """Main function to orchestrate data loading."""
    print("=" * 60)
    print("🚀 CoreInventory Database Data Loader")
    print("=" * 60)

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        # Create tables
        await create_tables(engine)

        # Create session and load data in correct order
        async with AsyncSessionLocal() as db:
            # Load data in order of dependencies
            if (CSV_DATA_PATH / "categories.csv").exists():
                await load_categories(db, CSV_DATA_PATH / "categories.csv")

            if (CSV_DATA_PATH / "products.csv").exists():
                await load_products(db, CSV_DATA_PATH / "products.csv")

            if (CSV_DATA_PATH / "warehouses.csv").exists():
                await load_warehouses(db, CSV_DATA_PATH / "warehouses.csv")

            if (CSV_DATA_PATH / "locations.csv").exists():
                await load_locations(db, CSV_DATA_PATH / "locations.csv")

            if (CSV_DATA_PATH / "inventory.csv").exists():
                await load_inventory(db, CSV_DATA_PATH / "inventory.csv")

            if (CSV_DATA_PATH / "operations.csv").exists():
                await load_operations(db, CSV_DATA_PATH / "operations.csv")

            if (CSV_DATA_PATH / "operation_items.csv").exists():
                await load_operation_items(db, CSV_DATA_PATH / "operation_items.csv")

        print("\n" + "=" * 60)
        print("✅ Database loading completed successfully!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("   - All tables created")
        print("   - All CSV data loaded into corresponding tables")
        print("\n🔗 Database URL:", settings.DATABASE_URL)
        print("\n📝 Next Step: Create an admin user")
        print("   Run: python create_admin.py")

    except Exception as e:
        print(f"\n❌ Error during data loading: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
