from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.auth import SignupRequest, LoginRequest, TokenResponse, ResetPasswordRequest
from services import auth_service
from auth.dependencies import get_current_user
from models import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Sign up a new user."""
    user = await auth_service.signup(db, data)

    # Return token immediately after signup
    access_token = ""
    from auth.jwt_handler import create_access_token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
    )

    from uuid import UUID
    return TokenResponse(
        access_token=access_token,
        user_id=UUID(user.id),
        email=user.email,
        role=user.role
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    return await auth_service.login(db, data)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Reset user password (requires authentication)."""
    success = await auth_service.reset_password(db, data)
    return {"success": success, "message": "Password reset successfully"}
