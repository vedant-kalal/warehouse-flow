from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Row

from models import Product


class VectorSearchResult:
    """Result from vector search."""

    def __init__(self, product_id: str, similarity: float):
        self.product_id = product_id
        self.similarity = similarity


async def search(
    db: AsyncSession,
    query_vector: list[float],
    product_ids: list[UUID] | None = None,
    threshold: float = 0.75,
    limit: int = 20
) -> list[VectorSearchResult]:
    """
    Vector similarity search using pgvector cosine distance.

    Operator: <=> (cosine distance, lower = more similar)
    Similarity score: 1 - distance (higher = more similar, range 0-1)

    Args:
        db: AsyncSession
        query_vector: 1536-dimensional embedding vector
        product_ids: Optional subset of product IDs to search within
        threshold: Similarity threshold (0-1), default 0.75
        limit: Max results to return, default 20

    Returns:
        List of VectorSearchResult with product_id and similarity score
    """

    # Convert Python list to PostgreSQL vector format
    # PostgreSQL vector format: "[0.1, 0.2, 0.3, ...]"
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    # Build SQL query with pgvector cosine distance operator
    # The <=> operator returns cosine distance (0-2 range, lower = more similar)
    # We convert to similarity score: 1 - distance (0-1 range, higher = more similar)
    sql_query = text("""
        SELECT
            p.id,
            ROUND((1 - (p.embedding <=> CAST(:vector AS vector)))::numeric, 4) AS similarity
        FROM products p
        WHERE
            p.embedding IS NOT NULL
            AND (1 - (p.embedding <=> CAST(:vector AS vector))) > :threshold
            AND (:product_ids IS NULL OR p.id = ANY(:product_ids))
        ORDER BY similarity DESC
        LIMIT :limit
    """)

    # Convert product IDs to string list for PostgreSQL
    product_ids_str = None
    if product_ids:
        product_ids_str = [str(pid) for pid in product_ids]

    # Execute query
    result = await db.execute(
        sql_query,
        {
            "vector": vector_str,
            "threshold": threshold,
            "product_ids": product_ids_str,
            "limit": limit,
        }
    )

    # Convert results to VectorSearchResult objects
    rows = result.fetchall()
    results = [
        VectorSearchResult(product_id=row[0], similarity=float(row[1]))
        for row in rows
    ]

    return results
