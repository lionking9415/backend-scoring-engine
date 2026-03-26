"""
Supabase Database Layer (G3)
Stores raw responses, processed scores, and final output JSON.
Uses the Supabase Python client for all CRUD operations.
Falls back gracefully if Supabase is unavailable.
"""

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_client():
    """Lazy import to avoid circular imports and allow graceful fallback."""
    from scoring_engine.supabase_client import get_supabase_client
    return get_supabase_client()


TABLE_NAME = "assessment_results"


def store_result(
    user_id: str,
    report_type: str,
    raw_responses: list[dict],
    full_output: dict,
) -> str:
    """
    Store a completed assessment result in Supabase.
    Returns the generated result ID.
    """
    client = _get_client()
    result_id = str(uuid.uuid4())

    record = {
        "id": result_id,
        "user_id": user_id,
        "report_type": report_type,
        "quadrant": full_output["load_framework"]["quadrant"],
        "load_state": full_output["load_framework"]["load_state"],
        "pei_score": full_output["construct_scores"]["PEI_score"],
        "bhp_score": full_output["construct_scores"]["BHP_score"],
        "load_balance": full_output["load_framework"]["load_balance"],
        "archetype_id": full_output.get("archetype", {}).get("archetype_id"),
        "completion_rate": full_output["metadata"].get("completion_rate", 1.0),
        "low_confidence": full_output["metadata"].get("low_confidence", False),
        "demographics": full_output["metadata"].get("demographics"),
        "raw_responses": raw_responses,
        "full_output": full_output,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = client.table(TABLE_NAME).insert(record).execute()
    logger.info(f"Result stored in Supabase: id={result_id}, user={user_id}")
    return result_id


def get_result_by_id(result_id: str) -> dict | None:
    """Retrieve a stored result by its ID."""
    client = _get_client()
    response = (
        client.table(TABLE_NAME)
        .select("full_output")
        .eq("id", result_id)
        .maybe_single()
        .execute()
    )
    if response.data is None:
        return None
    return response.data["full_output"]


def get_results_by_user(user_id: str) -> list[dict]:
    """Retrieve all results for a given user, ordered by most recent first."""
    client = _get_client()
    response = (
        client.table(TABLE_NAME)
        .select("id, report_type, quadrant, archetype_id, pei_score, bhp_score, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def store_aims_responses(assessment_id: str, aims_data: list[dict]) -> None:
    """
    Store AIMS function responses in the aims_responses table.
    Each entry: {item_id, subdomain, aims_function}
    """
    if not aims_data:
        return

    client = _get_client()
    records = [
        {
            "assessment_id": assessment_id,
            "item_id": item["item_id"],
            "subdomain": item["subdomain"],
            "aims_function": item["aims_function"],
        }
        for item in aims_data
    ]
    client.table("aims_responses").insert(records).execute()
    logger.info(f"Stored {len(records)} AIMS responses for assessment {assessment_id}")


def check_connection() -> bool:
    """Test the Supabase connection. Returns True if reachable."""
    try:
        client = _get_client()
        client.table(TABLE_NAME).select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.warning(f"Supabase connection check failed: {e}")
        return False
