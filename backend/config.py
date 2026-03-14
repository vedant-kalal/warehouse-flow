import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ValidationError


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    GROQ_API_KEY: str = ""  # for AI filter extraction via Groq
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


# Helper function to provide better error messages
def _load_settings():
    """Load settings with helpful error messages."""
    try:
        return Settings()
    except ValidationError as e:
        print("\n" + "=" * 70)
        print("❌ CONFIGURATION ERROR - Missing Required Environment Variables")
        print("=" * 70 + "\n")

        # Check if .env exists
        env_file = Path(".env")
        if not env_file.exists():
            print(f"ERROR: .env file not found!")
            print(f"\nTo fix this:")
            print(f"  1. Run: python env_setup.py")
            print(f"  2. Or manually copy: cp .env.example .env")
            print(f"  3. Edit .env with your real credentials\n")
        else:
            print(f"ERROR: .env file exists but is missing required fields:\n")
            for error in e.errors():
                field = error.get('loc', ['Unknown'])[0]
                print(f"  ❌ {field}: {error.get('msg', 'Required field')}")

            print(f"\nTo fix this:")
            print(f"  1. Run: python env_setup.py")
            print(f"  2. Or edit .env manually:")
            print(f"     nano .env\n")
            print(f"Required fields:")
            print(f"  - DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/core_inventory")
            print(f"  - JWT_SECRET_KEY=your-secret-key-here (generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")")
            print(f"  - GROQ_API_KEY=gsk_... (optional but needed for chatbot feature)\n")

        print("=" * 70 + "\n")
        sys.exit(1)


settings = _load_settings()
