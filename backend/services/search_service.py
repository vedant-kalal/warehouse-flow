from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from schemas.search import SearchFilters, SearchResponse, SearchResult
from services import embedding_service
from ai import filter_extractor, keyword_search, vector_search
from ai.query_builder import build_inventory_query


async def search(
    db: AsyncSession,
    query: str,
    use_ai_filter: bool = True
) -> SearchResponse:
    """
    8-STEP SEARCH ORCHESTRATOR PIPELINE

    STEP 1: AI filter extraction
    STEP 2: Apply hard SQL filters
    STEP 3: Vector search on subset
    STEP 4: Keyword search on subset
    STEP 5: Merge results
    STEP 6: Final enriched query
    STEP 7: Format response
    STEP 8: Return
    """

    # ── STEP 1: AI FILTER EXTRACTION ──────────────────────────────
    # Extract structured filters from natural language using Claude
    filters = SearchFilters()
    if use_ai_filter:
        try:
            filters = await filter_extractor.extract_filters(query, today=date.today())
        except Exception as e:
            print(f"Error extracting filters via AI: {e}")
            filters = SearchFilters()

    # Fallback: if no product_query extracted, use full query
    if not filters.product_query:
        filters.product_query = query

    # ── STEP 2: APPLY HARD SQL FILTERS ──────────────────────────────
    # Run inventory query with all non-query filters (warehouse, category, etc.)
    # This reduces 10,000 products → maybe 200 products (the filtered subset)

    has_hard_filters = any([
        filters.product_name,
        filters.sku,
        filters.category,
        filters.warehouse,
        filters.location,
        filters.available_only,
        filters.low_stock,
        filters.out_of_stock,
        filters.min_qty,
        filters.max_qty,
        filters.unit,
    ])

    filtered_product_ids: list[UUID] | None = None

    if has_hard_filters:
        try:
            # Build and execute inventory query with filters
            inventory_query = build_inventory_query(filters, product_ids=None)
            result = await db.execute(inventory_query)
            rows = result.fetchall()

            if not rows:
                # No products match hard filters
                return SearchResponse(
                    query=query,
                    filters_applied=filters,
                    total=0,
                    results=[]
                )

            # Extract product IDs from filtered results
            filtered_product_ids = list(set(str(row.product_id) for row in rows))

        except Exception as e:
            print(f"Error applying hard filters: {e}")
            # Gracefully continue (vector search will work on all products)

    # ── STEP 3: VECTOR SEARCH (on subset only) ─────────────────────
    # Only run if we have a semantic search query (product_query)
    semantic_results: dict[str, float] = {}  # product_id → similarity

    if filters.product_query:
        try:
            query_vector = await embedding_service.generate_embedding(filters.product_query)
            threshold = 0.50 if filters.fetch_all else filters.similarity_threshold

            sem_results = await vector_search.search(
                db=db,
                query_vector=query_vector,
                product_ids=[UUID(pid) for pid in filtered_product_ids] if filtered_product_ids else None,
                threshold=threshold,
                limit=filters.limit
            )

            semantic_results = {str(r.product_id): r.similarity for r in sem_results}

        except Exception as e:
            print(f"Error in vector search: {e}")

    # ── STEP 4: KEYWORD SEARCH (on subset only) ────────────────────
    keyword_results: set[str] = set()

    if filters.product_query:
        try:
            kw_results = await keyword_search.search(
                db=db,
                keyword=filters.product_query,
                product_ids=[UUID(pid) for pid in filtered_product_ids] if filtered_product_ids else None
            )
            keyword_results = set(str(pid) for pid in kw_results)

        except Exception as e:
            print(f"Error in keyword search: {e}")

    # ── STEP 5: MERGE AND DEDUPLICATE ──────────────────────────────
    # Union of semantic + keyword results
    final_product_ids: dict[str, tuple[float, str]] = {}  # id → (similarity, match_type)

    if filters.product_query:
        all_matched_ids = set(semantic_results.keys()) | keyword_results

        if not all_matched_ids:
            return SearchResponse(
                query=query,
                filters_applied=filters,
                total=0,
                results=[]
            )

        for pid in all_matched_ids:
            in_semantic = pid in semantic_results
            in_keyword = pid in keyword_results
            match_type = (
                "keyword+semantic" if (in_semantic and in_keyword) else
                "semantic" if in_semantic else
                "keyword"
            )
            similarity = semantic_results.get(pid, 0.0)
            final_product_ids[pid] = (similarity, match_type)

        # Sort by similarity DESC
        sorted_ids = sorted(final_product_ids.items(), key=lambda x: x[1][0], reverse=True)
        final_product_ids = {k: v for k, v in sorted_ids[:filters.limit]}

    elif filtered_product_ids:
        # Only hard filters, no semantic search
        for pid in filtered_product_ids[:filters.limit]:
            final_product_ids[pid] = (0.0, "filter")

    else:
        return SearchResponse(
            query=query,
            filters_applied=filters,
            total=0,
            results=[]
        )

    # ── STEP 6: FINAL ENRICHED QUERY ────────────────────────────────
    # Get full inventory details for matched products
    final_ids_uuid = [UUID(pid) for pid in final_product_ids.keys()]
    final_inventory_query = build_inventory_query(filters, product_ids=final_ids_uuid)

    try:
        result = await db.execute(final_inventory_query)
        inventory_rows = result.fetchall()
    except Exception as e:
        print(f"Error fetching final inventory data: {e}")
        inventory_rows = []

    # ── STEP 7: FORMAT RESPONSE ─────────────────────────────────────
    response_items: list[SearchResult] = []

    for row in inventory_rows:
        product_id_str = str(row.product_id)
        similarity, match_type = final_product_ids.get(product_id_str, (0.0, "filter"))

        result_item = SearchResult(
            product_id=row.product_id,
            product_name=row.product_name,
            sku=row.sku,
            category=row.category_name or "Unknown",
            quantity=row.quantity,
            free_to_use=row.free_to_use,
            warehouse=row.warehouse_name,
            location=row.location_name,
            similarity=similarity if filters.product_query else None,
            match_type=match_type
        )
        response_items.append(result_item)

    # ── STEP 8: RETURN RESPONSE ────────────────────────────────────
    return SearchResponse(
        query=query,
        filters_applied=filters,
        total=len(response_items),
        results=response_items
    )
