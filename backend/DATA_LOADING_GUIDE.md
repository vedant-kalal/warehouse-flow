# Database Data Loading Guide

This guide explains how to load sample data from CSV files into the CoreInventory PostgreSQL database.

## Overview

The `push_csv_file.py` script automates the entire process of:
1. Creating database tables
2. Loading CSV data into each table
3. Creating a default admin user
4. Maintaining proper foreign key constraints

## Prerequisites

1. **PostgreSQL installed and running**
2. **Python 3.10+ installed**
3. **Database connection configured in `.env`** file with `DATABASE_URL`

Example `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/core_inventory
JWT_SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
ENVIRONMENT=development
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Data Loading Script

```bash
python push_csv_file.py
```

### 3. Expected Output

```
============================================================
🚀 CoreInventory Database Data Loader
============================================================
🔧 Creating database tables...
✅ Tables created successfully!

👤 Creating default admin user...
✅ Default admin user created
   Email: admin@inventory.local
   Password: admin123 (change this in production!)

📥 Loading categories...
✅ Loaded 4 categories

📥 Loading products...
✅ Loaded 5000 products

📥 Loading warehouses...
✅ Loaded 100 warehouses

📥 Loading locations...
✅ Loaded 5000 locations

📥 Loading inventory...
✅ Loaded 25000 inventory records

📥 Loading operations...
✅ Loaded 10000 operations

📥 Loading operation items...
✅ Loaded 50000 operation items

============================================================
✅ Database loading completed successfully!
============================================================
```

## CSV File Structure

### 1. **categories.csv**
- Columns: `id`, `name`
- Sample: Product categories like "Electronics", "Clothing", etc.
- Dependency: None

### 2. **products.csv**
- Columns: `id`, `name`, `sku`, `category_id`, `unit`, `reorder_level`, `is_active`, `embedding`, `created_at`
- Sample: Individual products with stock info
- Dependency: `categoryId` must exist in categories table
- Note: `embedding` column is empty (generated on-demand during search)

### 3. **warehouses.csv**
- Columns: `id`, `name`, `short_code`, `address`, `created_at`
- Sample: Distribution centers and storage locations
- Dependency: None

### 4. **locations.csv**
- Columns: `id`, `name`, `short_code`, `warehouse_id`
- Sample: Specific storage racks within warehouses
- Dependency: `warehouse_id` must exist in warehouses table

### 5. **inventory.csv**
- Columns: `id`, `product_id`, `location_id`, `quantity`, `reserved_qty`, `updated_at`
- Sample: Stock levels at specific locations
- Dependency: `product_id` and `location_id` must exist
- Note: Available quantity = `quantity - reserved_qty` (computed field)

### 6. **operations.csv**
- Columns: `id`, `type`, `status`, `reference`, `source_location_id`, `dest_location_id`, `created_by`, `created_at`, `updated_at`
- Sample: Stock movements (receipt, delivery, transfer, adjustment)
- Dependency: `created_by` user must exist, location IDs must exist
- Types: `receipt`, `delivery`, `transfer`, `adjustment`
- Statuses: `draft`, `confirmed`, `completed`

### 7. **operation_items.csv**
- Columns: `id`, `operation_id`, `product_id`, `quantity`
- Sample: Line items in each operation
- Dependency: `operation_id` and `product_id` must exist

## Default Admin User

A default admin user is created automatically:

```
Email: admin@inventory.local
Password: admin123
Role: admin
```

⚠️ **IMPORTANT**: Change this password immediately in production!

### To Update the Password

Use the authentication endpoint after logging in:
```bash
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d {
    "old_password": "admin123",
    "new_password": "your-new-secure-password"
  }
```

## Data Loading Order

The script loads data in this specific order to maintain foreign key constraints:

1. **Users** (default admin created)
2. **Categories**
3. **Products** (references categories)
4. **Warehouses**
5. **Locations** (references warehouses)
6. **Inventory** (references products and locations)
7. **Operations** (references locations and users)
8. **Operation Items** (references operations and products)

## Database Tables Summary

| Table | Records | Purpose |
|-------|---------|---------|
| categories | 4 | Product categorization |
| products | 5,000 | Inventory items |
| warehouses | 100 | Storage facilities |
| locations | 5,000 | Storage racks/bins within warehouses |
| inventory | 25,000 | Stock levels per product per location |
| operations | 10,000 | Stock movements |
| operation_items | 50,000 | Line items in operations |

## Troubleshooting

### Error: "Connection refused" or "could not connect to server"

**Solution**: Ensure PostgreSQL is running:
```bash
# On Windows
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# On macOS
brew services start postgresql
```

### Error: "database does not exist"

**Solution**: Create the database first:
```bash
createdb core_inventory
```

### Error: "UNIQUE constraint violated"

**Solution**: Clear the database and start fresh:
```bash
dropdb core_inventory
createdb core_inventory
python push_csv_file.py
```

### Error: "foreign key constraint violation"

**Solution**: Ensure CSV files are in the correct `backend/data/` directory. The script loads data in dependency order.

## Verifying the Data

After loading, you can verify the data using PostgreSQL:

```sql
-- Check row counts
SELECT 'categories' as table_name, COUNT(*) as count FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'warehouses', COUNT(*) FROM warehouses
UNION ALL
SELECT 'locations', COUNT(*) FROM locations
UNION ALL
SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL
SELECT 'operations', COUNT(*) FROM operations
UNION ALL
SELECT 'operation_items', COUNT(*) FROM operation_items;
```

## API Testing

Once data is loaded, test the backend:

```bash
# Start the API server
cd backend
uvicorn main:app --reload

# In another terminal, test the search endpoint
curl -X POST http://localhost:8000/ai/search \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d {
    "query": "electronics",
    "use_ai_filter": true
  }
```

## Regenerating Embeddings

After data is loaded, embeddings are not yet generated (CSV column is empty). To generate embeddings:

```python
# In your application code
from services.embedding_service import bulk_embed_products

# Generate embeddings for all products without embeddings
# This uses the Sentence Transformer model locally (no API calls)
num_embedded = await bulk_embed_products(db)
print(f"Generated embeddings for {num_embedded} products")
```

This uses the free local Sentence Transformer model (`all-MiniLM-L6-v2`) and doesn't require any API keys.

## Performance Notes

- **Total records to load**: ~95,000
- **Load time**: Depends on PostgreSQL performance, typically 5-15 seconds
- **Memory usage**: Minimal (pandas handles streaming)
- **Embeddings**: Generated on-demand during search, cached in database

## Need Help?

- Check database logs: `/var/log/postgresql/`
- Verify `.env` file has correct DATABASE_URL
- Ensure PostgreSQL user has create table permissions
- Check CSV files format (UTF-8, comma-delimited)
