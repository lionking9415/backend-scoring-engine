"""
Access Control & Per-Product Payment Model
==========================================

Centralizes all paywall logic so every premium endpoint goes through one helper.

Two products live here:

1. **Per-product unlocks** — Phase 4/4.5 monetization model.
   Each assessment can independently unlock these SKUs:

       PERSONAL_LIFESTYLE          $X   (lens report)
       STUDENT_SUCCESS             $X   (lens report)
       PROFESSIONAL_LEADERSHIP     $X   (lens report)
       FAMILY_ECOSYSTEM            $X   (lens report)
       COSMIC_BUNDLE               $X   (4 lenses + cosmic synthesis)
       FINANCIAL_DEEP_DIVE         $X   (Phase 4.5 add-on)
       HEALTH_DEEP_DIVE            $X   (Phase 4.5 add-on)
       COMPATIBILITY               $X   (Phase 5 paired report)

2. **Admin authentication** — gate `/api/v1/admin/*` and `/api/v1/audit/*`
   behind a simple shared-secret token (`ADMIN_API_TOKEN` env var).

Backwards-compatibility:
- The legacy single-string `payment_status` column ('free' | 'paid') is read as
  "all SKUs paid" when it is set to 'paid'. New per-product unlocks are stored
  in a JSONB `paid_products` column on `assessment_results`. Both are checked.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable, Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Product (SKU) catalog
# ---------------------------------------------------------------------------

LENS_PRODUCTS = (
    "PERSONAL_LIFESTYLE",
    "STUDENT_SUCCESS",
    "PROFESSIONAL_LEADERSHIP",
    "FAMILY_ECOSYSTEM",
)

ALL_PRODUCTS = LENS_PRODUCTS + (
    "COSMIC_BUNDLE",
    "FINANCIAL_DEEP_DIVE",
    "HEALTH_DEEP_DIVE",
    "COMPATIBILITY",
)


def _get_env_price_id(product: str) -> Optional[str]:
    """Look up a Stripe price ID for a given SKU.

    Looks for env var STRIPE_PRICE_ID_<PRODUCT>, falling back to STRIPE_PRICE_ID
    for backwards compatibility (treated as a "buy everything" bundle).
    """
    specific = os.getenv(f"STRIPE_PRICE_ID_{product}")
    if specific:
        return specific
    return os.getenv("STRIPE_PRICE_ID")


def get_price_id_for_product(product: str) -> Optional[str]:
    if product not in ALL_PRODUCTS:
        return None
    return _get_env_price_id(product)


# ---------------------------------------------------------------------------
# Per-product unlock state
# ---------------------------------------------------------------------------

def _fetch_assessment_payment_record(assessment_id: str) -> dict:
    """Return raw `payment_status` + `paid_products` for an assessment.

    Falls back to {"payment_status": "free", "paid_products": []} if Supabase
    is unavailable or the row is missing.
    """
    record = {"payment_status": "free", "paid_products": []}
    try:
        from scoring_engine.supabase_client import get_supabase_client

        client = get_supabase_client()
        if client is None:
            return record

        result = (
            client.table("assessment_results")
            .select("payment_status, paid_products")
            .eq("id", assessment_id)
            .maybe_single()
            .execute()
        )
        if result and result.data:
            record["payment_status"] = result.data.get("payment_status") or "free"
            paid_products = result.data.get("paid_products")
            if isinstance(paid_products, list):
                record["paid_products"] = [str(p) for p in paid_products]
            elif isinstance(paid_products, str):
                record["paid_products"] = [paid_products]
    except Exception as exc:
        logger.debug(f"Payment record lookup failed for {assessment_id}: {exc}")
    return record


def get_paid_products(assessment_id: str) -> list[str]:
    """Return the list of SKUs unlocked for this assessment.

    Read precedence (most-specific wins):

    1. The explicit `paid_products` JSONB list — modern per-SKU model.
       If non-empty, this is authoritative. A row with
       ``paid_products=['PERSONAL_LIFESTYLE']`` returns exactly that,
       even if the legacy ``payment_status='paid'`` flag is also set.
       (We saw cases where the legacy flag was leftover from an older
       code path or a fallback write — using it as a global override
       would silently expand a $30 single-lens unlock into full access.)

    2. The legacy ``payment_status='paid'`` flag — only consulted when
       no explicit per-SKU data exists. Expanded to ALL SKUs for
       backwards compatibility with rows that pre-date the
       ``paid_products`` column migration.

    Bundle-equivalence rule:
       Buying all 4 lens SKUs individually ($30 × 4 = $120) is treated as
       equivalent to purchasing the Cosmic Bundle ($99.99). When every
       lens in ``LENS_PRODUCTS`` is present, ``COSMIC_BUNDLE`` is added
       to the returned list synthetically so every downstream consumer
       (paywall, Cosmic Dashboard, Full Galaxy PDF, frontend gating)
       grants the same access a bundle buyer would receive.
    """
    rec = _fetch_assessment_payment_record(assessment_id)

    products: list[str]
    if rec["paid_products"]:
        products = list(rec["paid_products"])
    elif rec["payment_status"] == "paid":
        products = list(ALL_PRODUCTS)
    else:
        return []

    if (
        "COSMIC_BUNDLE" not in products
        and set(LENS_PRODUCTS).issubset(products)
    ):
        products.append("COSMIC_BUNDLE")

    return products


def is_product_paid(assessment_id: str, product: str) -> bool:
    if product not in ALL_PRODUCTS:
        return False
    paid = get_paid_products(assessment_id)
    if product in paid:
        return True
    # Cosmic bundle implicitly grants the four lenses.
    if "COSMIC_BUNDLE" in paid and product in LENS_PRODUCTS:
        return True
    return False


def has_any_premium_unlock(assessment_id: str) -> bool:
    """Used by the frontend to decide whether to show paid-only nav."""
    return bool(get_paid_products(assessment_id))


def unlock_products(
    assessment_id: str,
    products: Iterable[str],
    payment_id: str = "",
) -> bool:
    """Mark one or more SKUs as paid.

    Writes to the `paid_products` JSONB column. If the column is missing or
    Supabase is offline, falls back to the legacy `payment_status='paid'`
    behaviour when the COSMIC_BUNDLE (or all lenses) are unlocked.
    """
    products = [p for p in products if p in ALL_PRODUCTS]
    if not products:
        return False

    try:
        from datetime import datetime, timezone

        from scoring_engine.supabase_client import get_supabase_client

        client = get_supabase_client()
        if client is None:
            logger.error("Supabase unavailable — cannot persist product unlock")
            return False

        existing = get_paid_products(assessment_id)
        merged = sorted(set(existing) | set(products))

        update: dict = {
            "paid_products": merged,
            "upgraded_at": datetime.now(timezone.utc).isoformat(),
        }
        if payment_id:
            update["payment_id"] = payment_id
        # Mirror legacy single-string flag when the entire catalog is unlocked.
        if set(merged) >= set(ALL_PRODUCTS) or "COSMIC_BUNDLE" in merged:
            update["payment_status"] = "paid"

        result = (
            client.table("assessment_results")
            .update(update)
            .eq("id", assessment_id)
            .execute()
        )

        if result.data:
            logger.info(
                f"Unlocked products {merged} for assessment {assessment_id}"
            )
            return True

        logger.error(
            f"Failed to unlock products for {assessment_id} — no rows updated"
        )
        return False

    except Exception as exc:
        # Most likely a missing `paid_products` column on older schemas.
        # We only fall back to the legacy single-flag unlock when the user
        # was purchasing COSMIC_BUNDLE (or the full catalog) — in those
        # cases ``payment_status='paid'`` correctly represents "all SKUs
        # unlocked".
        #
        # For per-lens unlocks (PERSONAL_LIFESTYLE, etc.) the legacy flag
        # is *too coarse*: writing it would silently expand a $30 single-
        # lens unlock into full access, because ``get_paid_products``
        # falls back to the legacy flag when no explicit list exists.
        # In that case we'd rather fail loudly so the webhook is retried
        # and the schema gets fixed, than silently grant the wrong tier.
        legacy_safe = (
            "COSMIC_BUNDLE" in products
            or set(products) >= set(ALL_PRODUCTS)
        )
        if not legacy_safe:
            logger.error(
                f"paid_products write failed ({exc}) for {products}; "
                f"refusing legacy fallback (would over-grant access). "
                f"Check schema and retry the webhook."
            )
            return False

        logger.warning(
            f"paid_products write failed ({exc}); attempting legacy "
            f"unlock for {products}"
        )
        try:
            from scoring_engine.payment_service import unlock_report
            return unlock_report(assessment_id, payment_id or "fallback")
        except Exception as exc2:
            logger.error(f"Legacy unlock also failed: {exc2}")
            return False


# ---------------------------------------------------------------------------
# Endpoint guards
# ---------------------------------------------------------------------------

def require_paid_product(assessment_id: str, product: str) -> None:
    """Raise HTTP 402 unless this assessment has paid for `product`."""
    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    if not is_product_paid(assessment_id, product):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "product": product,
                "message": (
                    f"This feature requires the '{product}' unlock. "
                    "Purchase it via /api/v1/payment/create-checkout."
                ),
            },
        )


def require_any_paid(assessment_id: str, products: Iterable[str]) -> None:
    """Raise HTTP 402 unless at least one of the listed SKUs is unlocked."""
    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    if not any(is_product_paid(assessment_id, p) for p in products):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "payment_required",
                "products": list(products),
                "message": (
                    "This feature requires one of the listed unlocks. "
                    "Purchase it via /api/v1/payment/create-checkout."
                ),
            },
        )


# ---------------------------------------------------------------------------
# Admin auth (shared-secret token)
# ---------------------------------------------------------------------------

def _get_admin_token() -> Optional[str]:
    """Return the configured admin shared secret.

    Accepts either `ADMIN_API_TOKEN` (canonical) or the legacy
    `ADMIN_API_KEY` name for backward compatibility with older deploys.
    """
    return os.getenv("ADMIN_API_TOKEN") or os.getenv("ADMIN_API_KEY")


def require_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> None:
    """FastAPI dependency that enforces the admin shared secret.

    Reads the secret from `ADMIN_API_TOKEN` (or legacy `ADMIN_API_KEY`).
    If neither is set, admin endpoints are disabled outright (returns 503)
    — this prevents accidental exposure on a fresh deploy.
    """
    expected = _get_admin_token()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin endpoints are disabled (set ADMIN_API_TOKEN to enable).",
        )
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")
