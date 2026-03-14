"""
Quick Start: Loading Sample Data into CoreInventory Database

This script helps you get started with sample inventory data in minutes.
"""

import sys
import subprocess
from pathlib import Path


def print_banner(text):
    """Print formatted banner text."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def main():
    print_banner("🚀 CoreInventory Database Setup")

    backend_path = Path(__file__).parent
    print(f"✅ Backend directory: {backend_path}\n")

    # Step 1: Check PostgreSQL
    print_banner("Step 1: Verify PostgreSQL Setup")
    print("Required: PostgreSQL must be installed and running")
    print("Check your .env file for DATABASE_URL\n")
    print("Example DATABASE_URL:")
    print("  postgresql+asyncpg://postgres:password@localhost:5432/core_inventory\n")
    input("Press Enter to continue...")

    # Step 2: Check for .env
    env_file = backend_path / ".env"
    if not env_file.exists():
        print_banner("⚠️  .env File Not Found!")
        print(f"Create {backend_path}/.env with:")
        print("""
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/core_inventory
JWT_SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
ENVIRONMENT=development
""")
        sys.exit(1)
    print("\n✅ .env file found\n")

    # Step 3: Check data folder
    data_folder = backend_path / "data"
    if not data_folder.exists():
        print_banner("❌ Data Folder Not Found")
        print(f"Expected: {data_folder}")
        print("Make sure CSV files are in backend/data/")
        sys.exit(1)

    csv_files = list(data_folder.glob("*.csv"))
    print_banner("Step 2: Check Data Files")
    print(f"Found {len(csv_files)} CSV files:")
    for csv in sorted(csv_files):
        print(f"  ✓ {csv.name}")
    print()

    # Step 4: Install dependencies
    print_banner("Step 3: Install Dependencies")
    print("Running: pip install -r requirements.txt\n")
    response = input("Install now? (y/n): ")
    if response.lower() == 'y':
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_path)

    # Step 5: Run data loader
    print_banner("Step 4: Load Data into Database")
    print("This will:")
    print("  1. Create all database tables")
    print("  2. Load CSV data into tables in correct order")
    print("  3. Create default admin user (admin@inventory.local / admin123)")
    print("  4. Populate ~95,000 sample records\n")
    response = input("Load data now? (y/n): ")
    if response.lower() == 'y':
        from push_csv_file import main as load_data
        import asyncio
        try:
            asyncio.run(load_data())
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    # Step 6: Verify
    print_banner("✅ Setup Complete!")
    print("Next steps:")
    print("  1. Start the API server:")
    print("     $ uvicorn main:app --reload")
    print()
    print("  2. Admin login credentials:")
    print("     Email: admin@inventory.local")
    print("     Password: admin123")
    print()
    print("  3. API will be available at: http://localhost:8000")
    print("  4. API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
