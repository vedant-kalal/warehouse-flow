# AI module with singleton Groq client

from groq import Groq
from config import settings

# Singleton Groq client (initialized once, reused for all requests)
_groq_client = None


def get_groq_client() -> Groq:
    """
    Get or create Groq client (singleton pattern).

    This function ensures only ONE Groq client is created and reused
    across all requests, avoiding unnecessary overhead.

    Returns:
        Groq: Configured Groq client instance

    Raises:
        ValueError: If GROQ_API_KEY is not configured
    """
    global _groq_client

    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured in .env")

        # Create client once and cache it
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)

    return _groq_client


# Export for easy importing
__all__ = ["get_groq_client"]
