from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from auth.dependencies import get_current_user
from models import User

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("")
async def list_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"data": []}

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"message": "Not implemented"}
