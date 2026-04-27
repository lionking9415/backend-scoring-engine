"""
Audit Log Module — Persistent record of every AI prompt/response cycle.

Purpose:
  - QA review: verify prompt assembly is correct
  - Compliance: detect drift in language patterns
  - Debugging: replay generations that failed validation
  - Cost tracking: count requests per user/lens

Storage strategy:
  - Primary: Supabase `ai_audit_log` table (when available)
  - Fallback: in-memory ring buffer (5,000 entries max)
  - Optional: file-based JSON Lines append for forensic trail

CRITICAL: This module MUST NOT raise. Audit failures should never break
report generation. All exceptions are swallowed and logged.
"""

import logging
import os
import uuid
import json
import threading
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory ring buffer (process-local fallback)
_AUDIT_BUFFER: list[dict] = []
_AUDIT_BUFFER_LOCK = threading.Lock()
_AUDIT_BUFFER_MAX = 5000

# Optional JSONL audit file (set AUDIT_LOG_FILE env var to enable)
_AUDIT_FILE = os.getenv("AUDIT_LOG_FILE")


def _truncate_for_storage(text: Optional[str], limit: int = 50_000) -> Optional[str]:
    """Avoid storing pathologically large prompt or response bodies."""
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def log_ai_call(
    audit_context: Optional[dict],
    system_prompt: str,
    user_prompt: str,
    response_text: Optional[str],
    error: Optional[str] = None,
    attempt: int = 1,
) -> Optional[str]:
    """Persist an AI call. Returns audit_id or None on failure.

    audit_context fields (optional):
      - user_id, assessment_id, report_type, kind
    """
    audit_id = str(uuid.uuid4())
    ctx = audit_context or {}
    record = {
        "id": audit_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": ctx.get("user_id"),
        "assessment_id": ctx.get("assessment_id"),
        "report_type": ctx.get("report_type"),
        "kind": ctx.get("kind", "unknown"),
        "attempt": attempt,
        "system_prompt": _truncate_for_storage(system_prompt),
        "user_prompt": _truncate_for_storage(user_prompt),
        "response_text": _truncate_for_storage(response_text),
        "error": error,
        "status": "success" if response_text and not error else "failure",
    }

    # Try database first
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client is not None:
            client.table("ai_audit_log").insert(record).execute()
    except Exception as e:
        logger.debug(f"Audit DB write skipped: {e}")

    # Always also write to in-memory buffer for fast readback
    try:
        with _AUDIT_BUFFER_LOCK:
            _AUDIT_BUFFER.append(record)
            if len(_AUDIT_BUFFER) > _AUDIT_BUFFER_MAX:
                # Drop oldest 10% to amortize cost of trimming
                drop = _AUDIT_BUFFER_MAX // 10
                del _AUDIT_BUFFER[:drop]
    except Exception as e:
        logger.debug(f"Audit buffer write failed: {e}")

    # Optional JSONL file append
    if _AUDIT_FILE:
        try:
            with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.debug(f"Audit file write failed: {e}")

    return audit_id


def get_audit_logs(
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Retrieve recent audit logs, optionally filtered."""
    # Try DB first
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client is not None:
            q = client.table("ai_audit_log").select("*")
            if user_id:
                q = q.eq("user_id", user_id)
            if assessment_id:
                q = q.eq("assessment_id", assessment_id)
            q = q.order("timestamp", desc=True).limit(limit)
            response = q.execute()
            if response.data:
                return response.data
    except Exception as e:
        logger.debug(f"Audit DB read skipped: {e}")

    # Fallback to in-memory buffer
    with _AUDIT_BUFFER_LOCK:
        results = list(_AUDIT_BUFFER)
    if user_id:
        results = [r for r in results if r.get("user_id") == user_id]
    if assessment_id:
        results = [r for r in results if r.get("assessment_id") == assessment_id]
    results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return results[:limit]


def get_audit_summary() -> dict:
    """Return aggregate stats over the in-memory buffer."""
    with _AUDIT_BUFFER_LOCK:
        snapshot = list(_AUDIT_BUFFER)

    total = len(snapshot)
    by_kind: dict[str, int] = {}
    failures = 0
    for r in snapshot:
        by_kind[r.get("kind", "unknown")] = by_kind.get(r.get("kind", "unknown"), 0) + 1
        if r.get("status") == "failure":
            failures += 1

    return {
        "total_calls": total,
        "failures": failures,
        "success_rate": (1 - failures / total) if total else 0.0,
        "by_kind": by_kind,
        "buffer_capacity": _AUDIT_BUFFER_MAX,
    }
