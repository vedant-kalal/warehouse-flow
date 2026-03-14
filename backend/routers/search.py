from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from auth.dependencies import get_current_user
from models import User
from services import search_service
from schemas.search import SearchResponse
from utils.response import success

router = APIRouter(prefix="/ai", tags=["ai"])


class SearchRequest(BaseModel):
    """Request model for AI search endpoint."""
    query: str
    use_ai_filter: bool = True


@router.post("/search", response_model=dict, status_code=status.HTTP_200_OK)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    AI-powered inventory search with automatic filter extraction.

    Supports:
    - Natural language product queries ("nike shoes", "electronics")
    - Inventory filters ("low stock", "available", "over 100 units")
    - Location filters ("Delhi warehouse", "Rack A")
    - Operation filters ("pending receipts", "deliveries last week")
    - Automatic semantic search via vector embeddings
    - Fallback keyword search (ILIKE matching)

    Query Examples:
    - "show me all nike shoes available in Delhi"
    - "low stock electronics in Rack A with less than 10 units"
    - "confirmed receipts from last week in Mumbai"
    - "find SKU NK-001"

    Returns:
    - 20 results by default (configurable)
    - Each result includes similarity score and match type
    - Results are deduped and ranked by relevance
    """

    # Call the 8-step search pipeline
    search_result: SearchResponse = await search_service.search(
        db=db,
        query=request.query,
        use_ai_filter=request.use_ai_filter
    )

    # Format response
    return success(
        data=search_result.model_dump(),
        message=f"Found {search_result.total} results"
    )

