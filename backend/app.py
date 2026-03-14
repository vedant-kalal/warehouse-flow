"""
CoreInventory CLI Chatbot

Interactive CLI application for querying the inventory database using natural language.
Each conversation turn is independent with intelligent filter extraction based on available
categories, tables, and fields.

Features:
- Interactive chat interface
- Dynamic prompt building based on database schema
- Intelligent filter extraction using Groq LLM
- Category and field-aware filtering
- Pretty-formatted results per table
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import inspect, text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from models import (
    Category, Product, Warehouse, Location,
    Inventory, Operation, OperationItem, User
)
from ai.client import get_groq_client


# Color codes for CLI
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DatabaseSchema:
    """Manages database schema introspection."""

    def __init__(self, engine):
        self.engine = engine
        self.schema = {}
        self.tables_map = {
            'categories': Category,
            'products': Product,
            'warehouses': Warehouse,
            'locations': Location,
            'inventory': Inventory,
            'operations': Operation,
            'operation_items': OperationItem,
        }

    async def load_schema(self):
        """Load all table schemas from database."""
        async with self.engine.begin() as conn:
            # Use run_sync to perform inspection within the async context
            def inspect_tables(sync_conn):
                inspector = inspect(sync_conn)
                schema = {}
                for table_name in inspector.get_table_names():
                    if table_name in self.tables_map:
                        columns = inspector.get_columns(table_name)
                        schema[table_name] = {
                            'columns': [col['name'] for col in columns],
                            'column_types': {col['name']: str(col['type']) for col in columns}
                        }
                return schema

            self.schema = await conn.run_sync(inspect_tables)

    def get_available_fields(self, table_name: str) -> List[str]:
        """Get available fields for a table."""
        if table_name in self.schema:
            return self.schema[table_name]['columns']
        return []

    def get_schema_description(self) -> str:
        """Get human-readable schema description."""
        description = "Database Schema:\n\n"
        for table_name, info in self.schema.items():
            description += f"Table: {table_name}\n"
            description += f"  Fields: {', '.join(info['columns'])}\n\n"
        return description


class CategoryManager:
    """Manages category data."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.categories = []
        self.category_names = []

    async def load_categories(self):
        """Load all categories from database."""
        query = select(Category.id, Category.name)
        result = await self.db_session.execute(query)
        self.categories = result.fetchall()
        self.category_names = [cat[1] for cat in self.categories]

    def get_category_list(self) -> str:
        """Get formatted category list."""
        if not self.category_names:
            return "No categories found"
        return ", ".join([f"[{name}]" for name in self.category_names])


class PromptBuilder:
    """Builds dynamic system prompts."""

    @staticmethod
    def build_system_prompt(
        schema: DatabaseSchema,
        categories: List[str],
        available_tables: List[str]
    ) -> str:
        """Build system prompt with current schema and categories."""

        schema_desc = ""
        for table_name in available_tables:
            fields = schema.get_available_fields(table_name)
            if fields:
                schema_desc += f"- {table_name}: {', '.join(fields)}\n"

        prompt = f"""You are an intelligent inventory database query assistant.

Your job is to extract filters from user queries based on available database schema and categories.

AVAILABLE CATEGORIES:
{', '.join([f'[{cat}]' for cat in categories]) if categories else 'None'}

AVAILABLE TABLES AND FIELDS:
{schema_desc}

INSTRUCTIONS:
1. Analyze the user query for any mentions of available categories
2. If a category is mentioned → include it in filters
3. If a category is NOT mentioned → leave it as null (no filter)
4. Extract other relevant filters based on the query:
   - Product names/SKUs
   - Warehouse names
   - Location details
   - Quantity ranges
   - Date ranges
   - Operation types (receipt, delivery, transfer, adjustment)
5. Return ONLY valid fields that exist in the table schema
6. For each query, determine which tables to query

RESPONSE FORMAT (JSON):
{{
  "tables_to_query": ["category", "product", "warehouse"],  // Only tables relevant to query
  "filters": {{
    "categories": {{
      "category_id": "category-uuid or null"
    }},
    "products": {{
      "category_id": "category-uuid or null",
      "name": "product name or null",
      "sku": "sku or null",
      "is_active": true or null
    }},
    "warehouses": {{
      "name": "warehouse name or null",
      "short_code": "code or null"
    }},
    "locations": {{
      "warehouse_id": "uuid or null",
      "name": "location name or null"
    }},
    "inventory": {{
      "product_id": "uuid or null",
      "location_id": "uuid or null",
      "quantity_min": number or null,
      "quantity_max": number or null
    }},
    "operations": {{
      "type": "receipt|delivery|transfer|adjustment or null",
      "status": "draft|confirmed|completed or null"
    }},
    "operation_items": {{
      "product_id": "uuid or null",
      "quantity_min": number or null,
      "quantity_max": number or null
    }}
  }},
  "explanation": "Brief explanation of filters extracted"
}}

IMPORTANT:
- Always return valid JSON
- Use null for filters you cannot determine from the query
- Only include tables that are relevant to the query
- Be intelligent about category matching (user might say "electronics" for a category named "Electronics")
- Return category_id (uuid) if category is matched, not the name
"""
        return prompt


class FilterExtractor:
    """Extracts filters from user queries using Groq LLM."""

    async def extract_filters(
        self,
        user_query: str,
        system_prompt: str
    ) -> Dict[str, Any]:
        """Extract filters from user query using Groq."""
        try:
            client = get_groq_client()

            message = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                response_format={"type": "json_object"}
            )

            response_text = message.choices[0].message.content
            filters = json.loads(response_text)
            return filters

        except json.JSONDecodeError as e:
            print(f"{Colors.FAIL}❌ Error parsing AI response: {e}{Colors.ENDC}")
            return {"filters": {}, "error": str(e)}
        except Exception as e:
            print(f"{Colors.FAIL}❌ AI Error: {e}{Colors.ENDC}")
            return {"filters": {}, "error": str(e)}


class QueryExecutor:
    """Executes queries based on extracted filters."""

    def __init__(self, db_session: AsyncSession, schema: DatabaseSchema):
        self.db_session = db_session
        self.schema = schema

    async def execute_queries(
        self,
        filters: Dict[str, Any],
        category_map: Dict[str, str]
    ) -> Dict[str, List[Dict]]:
        """Execute queries based on extracted filters."""
        results = {}
        tables_to_query = filters.get("tables_to_query", [])

        # Query each relevant table
        for table_name in tables_to_query:
            if table_name == "categories":
                results["categories"] = await self._query_categories(filters.get("filters", {}).get("categories", {}))
            elif table_name == "products":
                results["products"] = await self._query_products(filters.get("filters", {}).get("products", {}), category_map)
            elif table_name == "warehouses":
                results["warehouses"] = await self._query_warehouses(filters.get("filters", {}).get("warehouses", {}))
            elif table_name == "locations":
                results["locations"] = await self._query_locations(filters.get("filters", {}).get("locations", {}))
            elif table_name == "inventory":
                results["inventory"] = await self._query_inventory(filters.get("filters", {}).get("inventory", {}))
            elif table_name == "operations":
                results["operations"] = await self._query_operations(filters.get("filters", {}).get("operations", {}))
            elif table_name == "operation_items":
                results["operation_items"] = await self._query_operation_items(filters.get("filters", {}).get("operation_items", {}))

        return results

    async def _query_categories(self, filters: Dict) -> List[Dict]:
        """Query categories table."""
        query = select(Category)

        if filters.get("name"):
            query = query.where(Category.name.ilike(f"%{filters['name']}%"))

        result = await self.db_session.execute(query)
        categories = result.scalars().all()

        return [
            {"id": cat.id, "name": cat.name}
            for cat in categories
        ]

    async def _query_products(self, filters: Dict, category_map: Dict) -> List[Dict]:
        """Query products table."""
        query = select(Product)

        if filters.get("category_id") and filters["category_id"] in category_map.values():
            query = query.where(Product.category_id == filters["category_id"])

        if filters.get("name"):
            query = query.where(Product.name.ilike(f"%{filters['name']}%"))

        if filters.get("sku"):
            query = query.where(Product.sku.ilike(f"%{filters['sku']}%"))

        if filters.get("is_active") is not None:
            query = query.where(Product.is_active == filters["is_active"])

        query = query.limit(10)  # Limit results
        result = await self.db_session.execute(query)
        products = result.scalars().all()

        return [
            {
                "id": prod.id,
                "name": prod.name,
                "sku": prod.sku,
                "category_id": prod.category_id,
                "unit": prod.unit,
                "reorder_level": prod.reorder_level,
                "is_active": prod.is_active
            }
            for prod in products
        ]

    async def _query_warehouses(self, filters: Dict) -> List[Dict]:
        """Query warehouses table."""
        query = select(Warehouse)

        if filters.get("name"):
            query = query.where(Warehouse.name.ilike(f"%{filters['name']}%"))

        if filters.get("short_code"):
            query = query.where(Warehouse.short_code.ilike(f"%{filters['short_code']}%"))

        query = query.limit(10)
        result = await self.db_session.execute(query)
        warehouses = result.scalars().all()

        return [
            {
                "id": wh.id,
                "name": wh.name,
                "short_code": wh.short_code,
                "address": wh.address
            }
            for wh in warehouses
        ]

    async def _query_locations(self, filters: Dict) -> List[Dict]:
        """Query locations table."""
        query = select(Location)

        if filters.get("warehouse_id"):
            query = query.where(Location.warehouse_id == filters["warehouse_id"])

        if filters.get("name"):
            query = query.where(Location.name.ilike(f"%{filters['name']}%"))

        query = query.limit(10)
        result = await self.db_session.execute(query)
        locations = result.scalars().all()

        return [
            {
                "id": loc.id,
                "name": loc.name,
                "short_code": loc.short_code,
                "warehouse_id": loc.warehouse_id
            }
            for loc in locations
        ]

    async def _query_inventory(self, filters: Dict) -> List[Dict]:
        """Query inventory table."""
        query = select(Inventory)

        if filters.get("product_id"):
            query = query.where(Inventory.product_id == filters["product_id"])

        if filters.get("location_id"):
            query = query.where(Inventory.location_id == filters["location_id"])

        if filters.get("quantity_min"):
            query = query.where(Inventory.quantity >= filters["quantity_min"])

        if filters.get("quantity_max"):
            query = query.where(Inventory.quantity <= filters["quantity_max"])

        query = query.limit(10)
        result = await self.db_session.execute(query)
        inventories = result.scalars().all()

        return [
            {
                "id": inv.id,
                "product_id": inv.product_id,
                "location_id": inv.location_id,
                "quantity": inv.quantity,
                "reserved_qty": inv.reserved_qty,
                "available": inv.quantity - inv.reserved_qty
            }
            for inv in inventories
        ]

    async def _query_operations(self, filters: Dict) -> List[Dict]:
        """Query operations table."""
        query = select(Operation)

        if filters.get("type"):
            query = query.where(Operation.type == filters["type"])

        if filters.get("status"):
            query = query.where(Operation.status == filters["status"])

        query = query.limit(10)
        result = await self.db_session.execute(query)
        operations = result.scalars().all()

        return [
            {
                "id": op.id,
                "type": op.type,
                "status": op.status,
                "reference": op.reference,
                "created_at": str(op.created_at)
            }
            for op in operations
        ]

    async def _query_operation_items(self, filters: Dict) -> List[Dict]:
        """Query operation items table."""
        query = select(OperationItem)

        if filters.get("product_id"):
            query = query.where(OperationItem.product_id == filters["product_id"])

        if filters.get("quantity_min"):
            query = query.where(OperationItem.quantity >= filters["quantity_min"])

        if filters.get("quantity_max"):
            query = query.where(OperationItem.quantity <= filters["quantity_max"])

        query = query.limit(10)
        result = await self.db_session.execute(query)
        items = result.scalars().all()

        return [
            {
                "id": item.id,
                "operation_id": item.operation_id,
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            for item in items
        ]


class CoreInventoryChatbot:
    """Main chatbot application."""

    def __init__(self, db_url: str):
        self.engine = None
        self.db_session = None
        self.schema = None
        self.categories = None
        self.category_map = {}
        self.filter_extractor = FilterExtractor()

    async def initialize(self):
        """Initialize database and load schema."""
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        AsyncSessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.db_session = AsyncSessionLocal()

        # Load schema
        self.schema = DatabaseSchema(self.engine)
        await self.schema.load_schema()

        # Load categories
        self.categories = CategoryManager(self.db_session)
        await self.categories.load_categories()

        # Build category map
        for cat_id, cat_name in self.categories.categories:
            self.category_map[cat_name] = cat_id

    async def cleanup(self):
        """Cleanup resources."""
        if self.db_session:
            await self.db_session.close()
        if self.engine:
            await self.engine.dispose()

    def print_header(self):
        """Print application header."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║       🛒 CoreInventory CLI Chatbot - Natural Language Query       ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")

        print(f"{Colors.OKGREEN}Available Categories:{Colors.ENDC}")
        print(f"  {self.categories.get_category_list()}\n")

        print(f"{Colors.OKBLUE}💡 Tips:{Colors.ENDC}")
        print("  - Ask about products, prices, stock levels")
        print("  - Mention categories like 'Electronics', 'Clothing'")
        print("  - Ask about warehouse locations, operations")
        print("  - Type 'exit' or 'quit' to leave\n")

    def print_results(self, results: Dict[str, List[Dict]]):
        """Pretty print results."""
        if not results:
            print(f"{Colors.WARNING}No results found.{Colors.ENDC}\n")
            return

        for table_name, rows in results.items():
            if rows:
                print(f"\n{Colors.BOLD}{Colors.OKGREEN}📊 {table_name.upper()}{Colors.ENDC}")
                print(f"   {Colors.OKBLUE}({len(rows)} records){Colors.ENDC}\n")

                for i, row in enumerate(rows, 1):
                    print(f"   {Colors.OKCYAN}Record {i}:{Colors.ENDC}")
                    for key, value in row.items():
                        print(f"     • {key}: {Colors.OKGREEN}{value}{Colors.ENDC}")
                    print()

    async def chat_loop(self):
        """Main chat loop."""
        self.print_header()

        while True:
            try:
                # Get user query
                user_query = input(f"{Colors.BOLD}{Colors.OKBLUE}You: {Colors.ENDC}").strip()

                if not user_query:
                    continue

                if user_query.lower() in ['exit', 'quit', 'bye']:
                    print(f"\n{Colors.OKGREEN}Goodbye! 👋{Colors.ENDC}\n")
                    break

                # Show thinking
                print(f"{Colors.WARNING}🤖 Processing your query...{Colors.ENDC}")

                # Build dynamic prompt
                system_prompt = PromptBuilder.build_system_prompt(
                    self.schema,
                    self.categories.category_names,
                    list(self.schema.schema.keys())
                )

                # Extract filters using Groq
                filters = await self.filter_extractor.extract_filters(user_query, system_prompt)

                if "error" in filters:
                    print(f"{Colors.FAIL}❌ Error processing query{Colors.ENDC}\n")
                    continue

                # Print extracted filters
                print(f"\n{Colors.OKCYAN}📋 Extracted Filters:{Colors.ENDC}")
                print(f"   {json.dumps(filters, indent=2)}\n")

                # Execute queries
                executor = QueryExecutor(self.db_session, self.schema)
                results = await executor.execute_queries(filters, self.category_map)

                # Print results
                self.print_results(results)

            except KeyboardInterrupt:
                print(f"\n{Colors.OKGREEN}\nGoodbye! 👋{Colors.ENDC}\n")
                break
            except Exception as e:
                print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}\n")


async def main():
    """Main entry point."""
    print(f"\n{Colors.BOLD}Initializing CoreInventory Chatbot...{Colors.ENDC}")

    chatbot = CoreInventoryChatbot(settings.DATABASE_URL)

    try:
        await chatbot.initialize()
        print(f"{Colors.OKGREEN}✅ Chatbot initialized successfully!{Colors.ENDC}\n")
        await chatbot.chat_loop()
    except Exception as e:
        print(f"{Colors.FAIL}❌ Initialization error: {e}{Colors.ENDC}")
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
