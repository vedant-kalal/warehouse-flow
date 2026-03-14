from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from models import User
from schemas.auth import SignupRequest, LoginRequest, TokenResponse, ResetPasswordRequest
from auth.password import hash_password, verify_password
from auth.jwt_handler import create_access_token
from utils.exceptions import raise_409, raise_401, raise_404


async def signup(db: AsyncSession, data: SignupRequest) -> User:
    """Sign up a new user."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise_409(detail="Email already registered")

    # Create new user
    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role.value
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT token."""
    # Fetch user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise_401(detail="Invalid email or password")

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise_401(detail="Invalid email or password")

    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
    )

    return TokenResponse(
        access_token=access_token,
        user_id=UUID(user.id),
        email=user.email,
        role=user.role
    )


async def reset_password(db: AsyncSession, data: ResetPasswordRequest) -> bool:
    """Reset user password."""
    # Fetch user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise_404(detail="User not found")

    # Update password
    user.password_hash = hash_password(data.new_password)
    await db.commit()

    return True
