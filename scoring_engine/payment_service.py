"""
Payment Service Module — Stripe Integration (Phase 2)
Handles payment processing and report unlocking.

This module handles:
- Stripe checkout session creation
- Payment webhook processing
- Report unlock mechanism
- Payment status tracking
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Stripe client (lazy initialization)
_stripe = None


def get_stripe_client():
    """Get or initialize Stripe client."""
    global _stripe
    
    if _stripe is None:
        api_key = os.getenv("STRIPE_SECRET_KEY")
        if not api_key:
            logger.warning("STRIPE_SECRET_KEY not set - payment processing disabled")
            return None
        
        try:
            import stripe
            stripe.api_key = api_key
            _stripe = stripe
            logger.info("Stripe client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Stripe client: {e}")
            return None
    
    return _stripe


def create_checkout_session(
    assessment_id: str,
    customer_email: str,
    success_url: str,
    cancel_url: str,
    product: str = "COSMIC_BUNDLE",
) -> Optional[dict]:
    """
    Create a Stripe checkout session for a single product unlock.
    
    Args:
        assessment_id: UUID of the assessment to unlock
        customer_email: User's email address
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled
        product: Which SKU is being purchased. One of:
            PERSONAL_LIFESTYLE, STUDENT_SUCCESS, PROFESSIONAL_LEADERSHIP,
            FAMILY_ECOSYSTEM, COSMIC_BUNDLE, FINANCIAL_DEEP_DIVE,
            HEALTH_DEEP_DIVE, COMPATIBILITY.
    
    Returns:
        Dictionary with session_id and checkout_url, or None if creation fails
    """
    from scoring_engine.access_control import (
        ALL_PRODUCTS,
        get_price_id_for_product,
    )

    if product not in ALL_PRODUCTS:
        logger.error(f"Invalid product SKU '{product}'")
        return None

    stripe = get_stripe_client()
    if not stripe:
        logger.warning("Stripe not configured - returning mock session")
        return {
            "session_id": "mock_session_id",
            "checkout_url": f"{success_url}?mock=true&product={product}",
            "error": "Stripe not configured - payment disabled",
            "product": product,
        }

    try:
        price_id = get_price_id_for_product(product)
        if not price_id:
            logger.error(
                f"No Stripe price configured for product '{product}' "
                f"(set STRIPE_PRICE_ID_{product})"
            )
            return None

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            metadata={
                'assessment_id': assessment_id,
                'product': product,
            },
        )

        logger.info(
            f"Created checkout session {session.id} for assessment "
            f"{assessment_id} (product={product})"
        )

        return {
            "session_id": session.id,
            "checkout_url": session.url,
            "product": product,
        }

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return None


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Stripe webhook signature.
    
    Args:
        payload: Raw request body
        signature: Stripe-Signature header value
    
    Returns:
        True if signature is valid, False otherwise
    """
    stripe = get_stripe_client()
    if not stripe:
        return False
    
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not set - skipping signature verification")
        return True  # Allow in development
    
    try:
        stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return True
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False


def process_payment_webhook(event_data: dict) -> Optional[dict]:
    """
    Process Stripe webhook event.
    
    Args:
        event_data: Stripe event data
    
    Returns:
        Dictionary with assessment_id and payment_id if successful, None otherwise
    """
    event_type = event_data.get('type')
    
    if event_type == 'checkout.session.completed':
        session = event_data.get('data', {}).get('object', {})

        metadata = session.get('metadata', {}) or {}
        assessment_id = metadata.get('assessment_id')
        product = metadata.get('product', 'COSMIC_BUNDLE')
        payment_intent = session.get('payment_intent')
        customer_email = session.get('customer_email')

        if not assessment_id:
            logger.error("No assessment_id in webhook metadata")
            return None

        logger.info(
            f"Payment completed for assessment {assessment_id} "
            f"(product={product})"
        )

        return {
            'assessment_id': assessment_id,
            'product': product,
            'payment_id': payment_intent,
            'customer_email': customer_email,
            'status': 'paid'
        }
    
    logger.info(f"Unhandled webhook event type: {event_type}")
    return None


def unlock_report(assessment_id: str, payment_id: str) -> bool:
    """
    Unlock full report for an assessment after payment.
    
    Args:
        assessment_id: UUID of the assessment
        payment_id: Stripe payment intent ID
    
    Returns:
        True if unlock successful, False otherwise
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        from datetime import datetime, timezone
        
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase not available - cannot unlock report")
            return False
        
        logger.info(f"Attempting to unlock report for assessment_id: {assessment_id}")
        
        # Update assessment record
        result = supabase.table('assessment_results').update({
            'payment_status': 'paid',
            'payment_id': payment_id,
            'upgraded_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', assessment_id).execute()
        
        logger.info(f"Update result: {result}")
        
        if result.data:
            logger.info(f"Successfully unlocked report for assessment {assessment_id}, payment_id: {payment_id}")
            logger.info(f"Updated records: {len(result.data)}")
            return True
        else:
            logger.error(f"Failed to unlock report for assessment {assessment_id} - no data returned")
            logger.error(f"Result object: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error unlocking report for {assessment_id}: {e}", exc_info=True)
        return False


def get_payment_status(assessment_id: str) -> str:
    """
    Get payment status for an assessment.
    
    Args:
        assessment_id: UUID of the assessment
    
    Returns:
        'free' or 'paid'
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return 'free'
        
        result = supabase.table('assessment_results')\
            .select('payment_status')\
            .eq('id', assessment_id)\
            .single()\
            .execute()
        
        if result.data:
            return result.data.get('payment_status', 'free')
        
        return 'free'
        
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return 'free'
