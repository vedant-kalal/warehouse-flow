from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from auth.dependencies import get_current_user
from models import User

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("")
async def list_inventory(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"data": []}

@router.get("/low-stock")
async def get_low_stock(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"data": []}
