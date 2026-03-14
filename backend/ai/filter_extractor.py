import json
from datetime import date

from config import settings
from schemas.search import SearchFilters
from ai.prompts import FILTER_EXTRACTION_PROMPT, get_date_references
from ai.client import get_groq_client


async def extract_filters(user_query: str, today: date | None = None) -> SearchFilters:
    """
    Extract SearchFilters from user's natural language query using Groq LLM.

    Uses Groq's JSON mode with Pydantic schema validation for structured output.
    Uses singleton Groq client to avoid creating new connections per request.

    STEP 1: Format prompt with date references
    STEP 2: Get JSON schema from SearchFilters pydantic model
    STEP 3: Call Groq API with response_format=json_object (reuses singleton client)
    STEP 4: Parse JSON response into SearchFilters pydantic model
    STEP 5: Return filters (or empty SearchFilters on error)
    """

    if not settings.GROQ_API_KEY:
        # No API key configured — return empty filters (keyword-only search)
        return SearchFilters()

    if today is None:
        today = date.today()

    try:
        # Get date references for the prompt
        date_refs = get_date_references(today)

        # Format the prompt with today's date and user query
        formatted_prompt = FILTER_EXTRACTION_PROMPT.format(
            user_query=user_query,
            **date_refs
        )

        # Get JSON schema for SearchFilters pydantic model
        # This ensures Groq returns data in the exact structure we expect
        schema = SearchFilters.model_json_schema()

        # Get singleton Groq client (reused across all requests)
        # This avoids creating a new client on every API call
        client = get_groq_client()

        # Call Groq API with JSON mode and structured output
        message = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Fast, reliable Groq model
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
            # Enable JSON mode for structured output
            response_format={"type": "json_object"}
        )

        # Extract JSON from response
        response_text = message.choices[0].message.content.strip()

        # Parse JSON (guaranteed to be valid due to response_format=json_object)
        filters_dict = json.loads(response_text)

        # Convert to SearchFilters pydantic model
        # This validates against the schema and provides type safety
        filters = SearchFilters(**filters_dict)

        return filters

    except json.JSONDecodeError as e:
        print(f"Error parsing Groq response as JSON: {e}")
        return SearchFilters()  # Fallback to empty filters

    except Exception as e:
        print(f"Error extracting filters from Groq: {e}")
        return SearchFilters()  # Graceful degradation
