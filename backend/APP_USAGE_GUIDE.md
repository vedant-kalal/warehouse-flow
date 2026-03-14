# 🤖 CoreInventory CLI Chatbot - User Guide

## Overview

The `app.py` is an interactive CLI chatbot that allows you to query your inventory database using **natural language**.

### Key Features:

✅ **Natural Language Queries** - Ask questions in plain English
✅ **Intelligent Filter Detection** - AI automatically detects:
   - Categories mentioned in your query
   - Product names/SKUs
   - Warehouse/Location names
   - Quantity ranges
   - Operation types (receipt, delivery, transfer, adjustment)

✅ **Multi-Table Support** - Query across all inventory tables:
   - Categories
   - Products
   - Warehouses
   - Locations
   - Inventory levels
   - Operations
   - Operation Items

✅ **Schema-Aware** - Only returns fields that actually exist in your database tables

✅ **Dynamic Prompts** - System prompt automatically adapts based on:
   - Available categories in your database
   - Actual table schemas
   - Current inventory data

---

## Installation

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Setup Environment
```bash
cp .env.example .env
# Edit .env with your actual credentials
nano .env
```

### Step 3: Load Sample Data (Optional)
```bash
python push_csv_file.py
# This loads ~95,000 sample records into your database
```

---

## Running the Chatbot

### Start the App
```bash
python app.py
```

### Expected Output
```
╔════════════════════════════════════════════════════════════════╗
║       🛒 CoreInventory CLI Chatbot - Natural Language Query    ║
╚════════════════════════════════════════════════════════════════╝

Available Categories:
  [Electronics] [Clothing] [Food] [Books]

💡 Tips:
  - Ask about products, prices, stock levels
  - Mention categories like 'Electronics', 'Clothing'
  - Ask about warehouse locations, operations
  - Type 'exit' or 'quit' to leave

Initializing CoreInventory Chatbot...
✅ Chatbot initialized successfully!

You:
```

---

## Examples - What You Can Ask

### Example 1: Find Electronics Products
```
You: Show me all electronics in stock

🤖 Processing your query...

📋 Extracted Filters:
   {
     "tables_to_query": ["categories", "products"],
     "filters": {
       "categories": {
         "name": "Electronics"
       },
       "products": {
         "category_id": "uuid-of-electronics",
         "is_active": true
       }
     }
   }

📊 CATEGORIES
   (1 records)
   Record 1:
     • id: uuid-xxx
     • name: Electronics

📊 PRODUCTS
   (45 records)
   Record 1:
     • id: uuid-yyy
     • name: iPhone 13
     • sku: IPN-13-001
     • category_id: uuid-xxx
     • unit: pieces
     • is_active: true
   ... (more records)
```

### Example 2: Check Low Stock Items
```
You: What products have quantity less than 5?

🤖 Processing your query...

📋 Extracted Filters:
   {
     "tables_to_query": ["products", "inventory"],
     "filters": {
       "inventory": {
         "quantity_max": 5
       }
     }
   }

📊 INVENTORY
   (23 records)
   ... inventory items with quantity < 5
```

### Example 3: Operations History
```
You: Show me all completed deliveries

🤖 Processing your query...

📋 Extracted Filters:
   {
     "tables_to_query": ["operations"],
     "filters": {
       "operations": {
         "type": "delivery",
         "status": "completed"
       }
     }
   }

📊 OPERATIONS
   (156 records)
   ... delivery operations with completed status
```

### Example 4: Warehouse Specific Query
```
You: Find books in the Mumbai warehouse

🤖 Processing your query...

📋 Extracted Filters:
   {
     "tables_to_query": ["categories", "products", "warehouses", "locations", "inventory"],
     "filters": {
       "categories": {
         "name": "Books"
       },
       "warehouses": {
         "name": "Mumbai"
       }
     }
   }

📊 CATEGORIES
📊 PRODUCTS
📊 WAREHOUSES
📊 LOCATIONS
📊 INVENTORY
   ... all results filtered by category and warehouse
```

### Example 5: Stock Count Range
```
You: Products with inventory between 10 and 100 units

🤖 Processing your query...

📋 Extracted Filters:
   {
     "tables_to_query": ["products", "inventory"],
     "filters": {
       "inventory": {
         "quantity_min": 10,
         "quantity_max": 100
       }
     }
   }

📊 PRODUCTS
📊 INVENTORY
   ... products with stock levels in that range
```

---

## How It Works

### Step-by-Step Process:

1. **User Types Query**
   ```
   You: Show all electronics products
   ```

2. **System Builds Dynamic Prompt**
   - Loads all available categories from database
   - Loads all table schemas with actual field names
   - Creates context about what's queryable

3. **Groq LLM Analyzes Query**
   - Identifies mentioned categories (Electronics → looks up UUID)
   - Determines which tables are relevant
   - Extracts specific filters: names, quantities, dates, etc.
   - Returns JSON with structured filters

4. **App Executes Queries**
   - Queries each relevant table
   - Applies extracted filters
   - Limits results to top 10 per table
   - Combines results

5. **Pretty-Prints Results**
   - Organized by table
   - Shows record count per table
   - Color-coded for easy reading
   - Only shows valid fields from schema

---

## System Prompt Logic

The chatbot uses an intelligent system prompt that:

### 1. Shows Available Categories
```
AVAILABLE CATEGORIES:
[Electronics] [Clothing] [Food] [Books] [Furniture]
```

The chatbot:
- Checks if user mentions any of these categories
- If mentioned → includes in filter
- If NOT mentioned → leaves as null (no filter on category)

### 2. Shows Available Tables & Fields
```
AVAILABLE TABLES AND FIELDS:
- categories: id, name
- products: id, name, sku, category_id, unit, reorder_level, is_active, embedding, created_at
- warehouses: id, name, short_code, address, created_at
- locations: id, name, short_code, warehouse_id
- inventory: id, product_id, location_id, quantity, reserved_qty, updated_at
- operations: id, type, status, reference, source_location_id, dest_location_id, created_by, created_at, updated_at
- operation_items: id, operation_id, product_id, quantity
```

The chatbot:
- Only returns fields that exist in your actual database
- Automatically detects new fields if you add them
- Won't ask for fields that don't exist

### 3. Intelligent Filtering
For each table, the chatbot:
- Checks if the user query contains any relevant values
- Extracts those values as filters
- Leaves irrelevant filters as `null`
- Combines multiple filters with AND logic

Example:
```
Query: "Nike shoes under $100"
→ Extracted: name=Nike, price_max=100
→ Filters: {name: "Nike", price: {max: 100}} (if field exists)
→ Result: Products with Nike in name AND price <= 100
```

---

## Supported Query Types

### By Topic:
- **Products**: "Show all Nike shoes", "Electronics products"
- **Inventory**: "Low stock items", "Products with 50+ units"
- **Warehouses**: "Warehouses in Mumbai", "All distribution centers"
- **Operations**: "Completed deliveries", "Receipt operations from today"
- **Combined**: "Electronics in Mumbai warehouse", "Stock levels for Nike products"

### By Attribute:
- **Category**: "Electronics", "Books", "Clothing"
- **Quantity**: "Under 10 units", "Between 50-100", "More than 1000"
- **Status**: "Active products", "Completed operations", "Draft receipts"
- **Type**: "Delivery", "Receipt", "Transfer", "Adjustment"
- **Location**: "Mumbai warehouse", "Storage rack A"

### By Action:
- "Show me...", "Find all...", "List...", "What products...", "How many..."
- "Check inventory...", "Look for...", "Find products with..."

---

## Tips for Better Queries

✅ **Good Queries:**
- "Show all electronics that are in stock"
- "Find products with less than 5 units"
- "List all completed deliveries in Mumbai warehouse"
- "What products are in the clothing category?"
- "Show me low stock items below 10 units"

❌ **Vague Queries:**
- "Show me stuff" (too vague - returns all)
- "Find things" (no specificity)
- "Products" (could match all products)

**Better Phrasing:**
- "Products in Electronics category that are active"
- "Inventory with 0-5 units in any location"
- "Operations with status completed"

---

## Understanding Output

### Sample Output:

```
📊 PRODUCTS
   (12 records)

   Record 1:
     • id: 550e8400-e29b-41d4-a716-446655440000
     • name: iPhone 13
     • sku: IPN-13-001
     • category_id: 550e8400-e29b-41d4-a716-446655440001
     • unit: pieces
     • reorder_level: 5
     • is_active: true

   Record 2:
     ... (more records)
```

### What Each Section Means:
- **Table Name** (PRODUCTS) - Which table these results come from
- **Record Count** (12 records) - How many matches found
- **Individual Records** - Each result with all available fields
- **Field Values** - Color-coded for readability

### No Results?
If a table shows 0 records:
- The query didn't match anything in that table
- Try wider search terms
- Check category spelling
- Verify the data exists in your database

---

## Exiting the App

```
You: exit

Goodbye! 👋
```

Or press `Ctrl+C` at any time to exit.

---

## Troubleshooting

### Issue: "Error: Connection refused"
**Solution:**
```bash
# Ensure PostgreSQL is running
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# Or on macOS:
brew services start postgresql
```

### Issue: "No results found"
**Solution:**
- Load sample data: `python push_csv_file.py`
- Check if categories exist: type "show categories"
- Verify database has data

### Issue: "Error parsing AI response"
**Solution:**
- Ensure Groq API key is valid in `.env`
- Check internet connection
- Try a simpler query

### Issue: "GROQ_API_KEY not set"
**Solution:**
```bash
# Edit .env file
nano .env

# Add your actual Groq API key:
GROQ_API_KEY=gsk_your_real_key_here
```

### Issue: "Database URL invalid"
**Solution:**
```bash
# Edit .env file
nano .env

# Fix the DATABASE_URL (example):
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/core_inventory
```

---

## Advanced: Customizing Categories

If you add/modify categories in your database:

1. **Add in database**:
   ```sql
   INSERT INTO categories (id, name) VALUES ('uuid', 'Toys');
   ```

2. **App automatically detects it** - Restart and the new category appears in the prompt

3. **Use in queries**: "Show me Toys category products"

---

## Architecture

```
User Query
    ↓
Dynamic Prompt Builder
    ↓ (adds categories + schema)
Groq LLM (Filter Extraction)
    ↓ (JSON filters)
Query Executor
    ↓ (database queries)
Result Formatter
    ↓ (pretty print)
Terminal Display
```

---

## Performance Notes

- **Query Time**: 2-5 seconds per query (depends on Groq API)
- **Result Limit**: 10 records per table (prevent overwhelming output)
- **Schema Load**: Happens once at startup
- **Categories Cache**: Loaded at startup, use `exit` and rerun for updates

---

## Using with Real Data

If you're using your own data instead of sample data:

1. **Ensure data is in database**
2. **Run app.py**
3. **Categories auto-load** from your database
4. **Fields auto-detect** from your schema
5. **Queries work immediately** - no extra configuration needed!

---

## Summary

```
┌─────────────────────────────────────────────────────┐
│  1. python app.py                                   │
│  2. You: Your natural language query                │
│  3. Chatbot extracts filters intelligently          │
│  4. Results returned, organized by table            │
│  5. Repeat or type 'exit' to leave                  │
└─────────────────────────────────────────────────────┘
```

That's it! Start chatting with your inventory database! 🚀
