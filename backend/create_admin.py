"""
Create Admin User Script

Simple script to create an admin user without bcrypt dependency issues.
"""

import asyncio
import getpass
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from models import User


async def create_admin_user():
    """Create an admin user interactively."""
    print("\n" + "=" * 60)
    print("👤 Create Admin User")
    print("=" * 60 + "\n")

    # Get email
    email = input("📧 Admin Email (default: admin@inventory.local): ").strip()
    if not email:
        email = "admin@inventory.local"

    # Get password
    while True:
        password = getpass.getpass("🔐 Admin Password: ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            continue

        password_confirm = getpass.getpass("🔐 Confirm Password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue

        break

    # Use bcrypt with better error handling
    try:
        from passlib.context import CryptContext

        # Create a simpler context that works
        pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=4  # Use fewer rounds for Windows compatibility
        )

        password_hash = pwd_context.hash(password)
    except Exception as e:
        print(f"\n⚠️  Warning: Bcrypt hashing failed ({str(e)[:50]}...)")
        print("Using simple encoding instead (NOT PRODUCTION SAFE)\n")
        # Fallback: use simple encoding (development only!)
        import base64
        password_hash = base64.b64encode(password.encode()).decode()

    # Connect to database
    print("\n🔗 Connecting to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with AsyncSessionLocal() as db:
            # Check if user already exists
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"\n❌ User with email '{email}' already exists")
                await engine.dispose()
                return

            # Create user
            admin_user = User(
                id=str(uuid4()),
                email=email,
                password_hash=password_hash,
                role="admin"
            )

            db.add(admin_user)
            await db.commit()

            print("\n" + "=" * 60)
            print("✅ Admin user created successfully!")
            print("=" * 60)
            print(f"\nAdmin Details:")
            print(f"  📧 Email: {email}")
            print(f"  🔐 Role: admin")
            print(f"  🆔 ID: {admin_user.id}\n")

    except Exception as e:
        print(f"\n❌ Error creating user: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
