"""
Supabase Client Module
Initializes and provides a singleton Supabase client instance.
Credentials are loaded from environment variables (.env file).
"""

import os
import logging

from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Get or create the singleton Supabase client.
    Raises RuntimeError if credentials are not configured.
    """
    global _client
    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "Supabase credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY in .env file."
        )

    _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    logger.info(f"Supabase client initialized: {SUPABASE_URL}")
    return _client


def reset_client():
    """Reset the singleton client (useful for testing)."""
    global _client
    _client = None
