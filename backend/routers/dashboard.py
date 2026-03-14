from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from auth.dependencies import get_current_user
from models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"message": "Not implemented"}
