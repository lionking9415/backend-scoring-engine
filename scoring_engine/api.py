"""
FastAPI REST API Layer (G2)
Secure endpoints for assessment submission and result retrieval.

Endpoints:
  POST /api/v1/assess          — Submit assessment responses, get scored output
  GET  /api/v1/results/{id}    — Retrieve a stored result by ID
  GET  /api/v1/results/user/{user_id} — Retrieve all results for a user
  GET  /api/v1/health          — Health check
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scoring_engine.access_control import (
    ALL_PRODUCTS,
    LENS_PRODUCTS,
    get_paid_products,
    has_any_premium_unlock,
    is_product_paid,
    require_admin,
    require_any_paid,
    require_paid_product,
    unlock_products,
)
from scoring_engine.config import REPORT_LENSES, SYSTEM_ID, DISPLAY_NAME
from scoring_engine.engine import process_assessment
from scoring_engine.validation import ValidationError

logger = logging.getLogger(__name__)

# =============================================================================
# Pydantic Models (Request / Response)
# =============================================================================


class ResponseItem(BaseModel):
    """A single assessment response."""
    item_id: str = Field(..., description="Item identifier (e.g. Q01)")
    response: int = Field(..., ge=1, le=4, description="User response value (A=4, B=3, C=2, D=1)")


class AssessmentRequest(BaseModel):
    """Assessment submission payload.

    The output tier is determined **server-side** from the assessment's payment
    state, not from the client. New assessments always start free.
    """
    user_id: str = Field(..., description="Unique user identifier")
    user_email: Optional[str] = Field(None, description="User email address")
    report_type: str = Field(..., description="Report lens (e.g. STUDENT_SUCCESS)")
    responses: list[ResponseItem] = Field(..., min_length=1, description="Assessment responses")
    demographics: Optional[dict] = Field(None, description="Optional demographic metadata")
    include_interpretation: bool = Field(True, description="Include AI narrative layer")
    use_ai: bool = Field(False, description="Use OpenAI for interpretation (Phase 2)")


class AssessmentResponse(BaseModel):
    """Wrapper for the assessment result."""
    success: bool
    result_id: Optional[str] = None
    data: dict


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    system_id: str
    system_name: str
    database: str


# =============================================================================
# App Factory
# =============================================================================


def create_app(use_database: bool = False) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        use_database: Whether to connect to Supabase for persistence.
                      Set False for lightweight/testing mode (in-memory).
    """
    app = FastAPI(
        title="BEST Galaxy Scoring Engine API",
        description=(
            "Backend scoring API for The BEST Executive Function Galaxy Assessment™. "
            "Processes 52-question assessments through PEI × BHP load interaction model."
        ),
        version="1.0.0",
    )

    # ALLOWED_ORIGINS: comma-separated list of frontend origins.
    # Set this to your Cloud Run frontend URL in production, e.g.:
    #   ALLOWED_ORIGINS=https://best-galaxy-frontend-xyz-uc.a.run.app
    # Defaults to "*" so local dev and test environments work without config.
    _raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
    allowed_origins = (
        [o.strip() for o in _raw_origins.split(",") if o.strip()]
        if _raw_origins != "*"
        else ["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Database state
    db_available = False

    if use_database:
        try:
            from scoring_engine.database import check_connection
            db_available = check_connection()
            if db_available:
                logger.info("Supabase connected and verified")
            else:
                logger.warning("Supabase connection check failed, running in-memory mode")
        except Exception as e:
            logger.warning(f"Supabase unavailable, running without persistence: {e}")
            db_available = False

    # In-memory fallback storage when Supabase is unavailable
    memory_store: dict[str, dict] = {}

    # -----------------------------------------------------------------
    # Endpoints
    # -----------------------------------------------------------------

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health_check():
        """System health check."""
        return HealthResponse(
            status="healthy",
            system_id=SYSTEM_ID,
            system_name=DISPLAY_NAME,
            database="supabase_connected" if db_available else "unavailable (in-memory mode)",
        )

    @app.post("/api/v1/assess", response_model=AssessmentResponse)
    def submit_assessment(request: AssessmentRequest):
        """
        Submit assessment responses and receive scored output.
        This is the primary endpoint — processes the full scoring pipeline.
        """
        # Validate report type
        if request.report_type not in REPORT_LENSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type '{request.report_type}'. "
                       f"Must be one of: {REPORT_LENSES}",
            )

        # Convert Pydantic models to dicts for the engine
        responses = [r.model_dump() for r in request.responses]

        try:
            result = process_assessment(
                user_id=request.user_id,
                report_type=request.report_type,
                responses=responses,
                demographics=request.demographics,
                include_interpretation=request.include_interpretation,
                use_ai=request.use_ai,
                user_email=request.user_email,
            )
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Store result
        result_id = result["metadata"].get("assessment_id", "") + "_" + request.user_id
        if db_available:
            try:
                from scoring_engine.database import store_result
                result_id = store_result(
                    user_id=request.user_id,
                    report_type=request.report_type,
                    raw_responses=responses,
                    full_output=result,
                )
            except Exception as e:
                logger.error(f"Failed to store result in Supabase: {e}")
                import uuid
                result_id = str(uuid.uuid4())
                memory_store[result_id] = result
        else:
            import uuid
            result_id = str(uuid.uuid4())
            memory_store[result_id] = result

        # Tier is decided by the server based on this assessment's payment
        # status. A brand-new assessment is always free. Paid output is only
        # returned via /api/v1/results/{id} after a successful unlock, never
        # directly from /assess.
        from scoring_engine.output import build_scorecard_output
        response_data = build_scorecard_output(result)

        return AssessmentResponse(
            success=True,
            result_id=result_id,
            data=response_data,
        )

    @app.get("/api/v1/results/{result_id}")
    def get_result(result_id: str):
        """Retrieve a stored assessment result by ID.

        Returns the FREE ScoreCard projection unless the assessment has been
        unlocked. If at least one lens (or the cosmic bundle) has been
        purchased, the full output is returned along with a `paid_products`
        list so the frontend can render only the unlocked sections.
        """
        data = None

        if db_available:
            try:
                from scoring_engine.database import get_result_by_id
                data = get_result_by_id(result_id)
            except Exception as e:
                logger.error(f"Supabase lookup failed: {e}")

        if data is None and result_id in memory_store:
            data = memory_store[result_id]

        if data is None:
            raise HTTPException(
                status_code=404, detail=f"Result '{result_id}' not found"
            )

        paid_products = get_paid_products(result_id)
        if not paid_products:
            from scoring_engine.output import build_scorecard_output
            return {
                "success": True,
                "tier": "free",
                "paid_products": [],
                "data": build_scorecard_output(data),
            }

        return {
            "success": True,
            "tier": "paid",
            "paid_products": paid_products,
            "data": data,
        }

    @app.get("/api/v1/results/user/{user_id}")
    def get_user_results(user_id: str):
        """Retrieve all assessment results for a user."""
        if db_available:
            try:
                from scoring_engine.database import get_results_by_user
                results = get_results_by_user(user_id)
                return {"success": True, "results": results}
            except Exception as e:
                logger.error(f"Supabase lookup failed: {e}")

        # Fallback: filter memory store
        user_results = []
        for rid, data in memory_store.items():
            if data.get("metadata", {}).get("user_id") == user_id:
                user_results.append({
                    "id": rid,
                    "report_type": data["metadata"]["report_type"],
                    "quadrant": data["load_framework"]["quadrant"],
                    "pei_score": data["construct_scores"]["PEI_score"],
                    "bhp_score": data["construct_scores"]["BHP_score"],
                })
        return {"success": True, "results": user_results}

    @app.get("/api/v1/questions")
    def get_questions():
        """Retrieve all assessment questions for the frontend."""
        from scoring_engine.item_dictionary import ITEM_DICTIONARY
        
        questions = [
            {
                "item_id": item["item_id"],
                "item_text": item["item_text"],
                "response_options": item["response_options"],
                "subdomain": item["subdomain"],
            }
            for item in ITEM_DICTIONARY
        ]
        return {"success": True, "questions": questions}

    # -----------------------------------------------------------------
    # Authentication Endpoints
    # -----------------------------------------------------------------

    @app.post("/api/v1/auth/signup")
    def signup(request: dict):
        """Create a new user account."""
        from scoring_engine.auth_service import (
            create_user,
            DuplicateEmailError,
            is_valid_email,
            normalize_email,
        )

        email = normalize_email(request.get('email'))
        password = request.get('password')
        name = request.get('name')
        demographics = request.get('demographics')

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        if not is_valid_email(email):
            raise HTTPException(status_code=400, detail="Please enter a valid email address")

        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        try:
            user = create_user(email, password, name, demographics)
        except DuplicateEmailError:
            # 409 = the request is well-formed but conflicts with existing state.
            # We include a structured `code` so the frontend can offer a
            # "Log in instead" CTA without string-matching the message.
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "email_exists",
                    "message": "An account with this email already exists. Please log in instead.",
                },
            )

        if not user:
            # Genuine creation failure (DB unreachable, validation, etc.).
            raise HTTPException(status_code=500, detail="Failed to create account. Please try again.")

        # Send email confirmation
        try:
            from scoring_engine.auth_service import generate_confirm_token
            from scoring_engine.email_service import send_confirmation_email
            token = generate_confirm_token(email)
            send_confirmation_email(email, user.get('name', ''), token)
        except Exception as mail_err:
            logger.warning("Confirmation email failed for %s: %s", email, mail_err)

        logger.info("New user signed up: %s", email)
        return {"success": True, "user": user, "email_confirmation_sent": True}

    @app.post("/api/v1/auth/login")
    def login(request: dict):
        """Authenticate a user and return session token."""
        from scoring_engine.auth_service import authenticate_user, normalize_email

        email = normalize_email(request.get('email'))
        password = request.get('password')

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        user = authenticate_user(email, password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Block login until the user has confirmed their email address.
        if not user.get('email_confirmed'):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "email_not_confirmed",
                    "message": "Please confirm your email address before logging in. Check your inbox for the confirmation link.",
                    "email": email,
                },
            )

        # Always try to pull the latest full intake record from
        # `demographic_intakes`.  That table is written by the 16-question
        # DemographicForm; the `users.demographics` column only has the 4
        # quick signup fields.  Merging here lets the frontend know the user
        # already completed the full intake and should not be sent back to it.
        if db_available:
            try:
                from scoring_engine.demographics import get_demographics
                intake = get_demographics(email)
                if intake is not None:
                    # Merge: intake keys win over signup keys for overlapping
                    # fields so the richer data is always surfaced.
                    merged = {**(user.get('demographics') or {}), **intake}
                    user['demographics'] = merged
                    user['has_completed_demographics'] = True
            except Exception as _e:
                logger.debug("Could not fetch demographics for login merge: %s", _e)

        logger.info("User logged in: %s", email)
        return {"success": True, "user": user}

    @app.put("/api/v1/auth/user/name")
    def update_account_name(request: dict):
        """Rename the signed-in account.

        Body: { "email": "<account email>", "name": "<new display name>" }

        Returns the refreshed user object (without the password hash) so the
        frontend can update its local cache atomically.
        """
        from scoring_engine.auth_service import (
            update_user_name,
            normalize_email,
        )

        email = normalize_email(request.get('email'))
        new_name = request.get('name')
        if not email:
            raise HTTPException(status_code=400, detail="email is required")

        try:
            updated = update_user_name(email, new_name)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        if not updated:
            raise HTTPException(status_code=404, detail="Account not found")

        # Re-merge demographics so the response shape matches /login & get_user.
        if db_available:
            try:
                from scoring_engine.demographics import get_demographics
                intake = get_demographics(email)
                if intake is not None:
                    merged = {**(updated.get('demographics') or {}), **intake}
                    updated['demographics'] = merged
                    updated['has_completed_demographics'] = True
            except Exception as _e:
                logger.debug("name-update demographic merge failed: %s", _e)

        logger.info("User renamed: %s", email)
        return {"success": True, "user": updated}

    @app.post("/api/v1/auth/change-password")
    def change_account_password(request: dict):
        """Change the signed-in account's password.

        Body: {
          "email": "<account email>",
          "current_password": "<existing pw>",
          "new_password": "<new pw, min 6 chars>"
        }

        Returns 401 if `current_password` is wrong, 400 on weak/empty new
        password, 404 if the email doesn't resolve to an account.
        """
        from scoring_engine.auth_service import (
            change_password,
            normalize_email,
            InvalidPasswordError,
            UserNotFoundError,
        )

        email = normalize_email(request.get('email'))
        current_password = request.get('current_password')
        new_password = request.get('new_password')
        if not email:
            raise HTTPException(status_code=400, detail="email is required")

        try:
            ok = change_password(email, current_password or "", new_password or "")
        except InvalidPasswordError:
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="Account not found")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        if not ok:
            raise HTTPException(status_code=500, detail="Failed to change password")

        logger.info("Password changed for: %s", email)
        return {"success": True}

    @app.get("/api/v1/auth/user/{email}")
    def get_user(email: str):
        """Get user information by email."""
        from scoring_engine.auth_service import get_user_by_email, normalize_email

        user = get_user_by_email(email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Same intake-merge logic as login, so the frontend can tell whether
        # the full 16-question intake has already been completed.
        if db_available:
            try:
                from scoring_engine.demographics import get_demographics
                intake = get_demographics(normalize_email(email))
                if intake is not None:
                    merged = {**(user.get('demographics') or {}), **intake}
                    user['demographics'] = merged
                    user['has_completed_demographics'] = True
            except Exception as _e:
                logger.debug("Could not fetch demographics for get_user merge: %s", _e)

        return {"success": True, "user": user}

    # -----------------------------------------------------------------
    # Email Confirmation & Password Reset Endpoints
    # -----------------------------------------------------------------

    @app.post("/api/v1/auth/confirm-email")
    def confirm_email(request: dict):
        """Verify the email-confirmation token and mark the account confirmed.

        Body: { "token": "<base64 token from email link>" }
        """
        from scoring_engine.auth_service import verify_confirm_token, confirm_user_email

        token = request.get('token')
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        email = verify_confirm_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired confirmation link. Please request a new one.")

        ok = confirm_user_email(email)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to confirm email. Please try again.")

        logger.info("Email confirmed: %s", email)
        return {"success": True, "email": email}

    @app.post("/api/v1/auth/resend-confirmation")
    def resend_confirmation(request: dict):
        """Re-send the email confirmation link.

        Body: { "email": "<user email>" }
        """
        from scoring_engine.auth_service import (
            normalize_email, get_user_by_email, generate_confirm_token,
            is_email_confirmed,
        )
        from scoring_engine.email_service import send_confirmation_email

        email = normalize_email(request.get('email'))
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Always return success to avoid leaking whether an account exists.
        user = get_user_by_email(email)
        if user and not is_email_confirmed(email):
            try:
                token = generate_confirm_token(email)
                send_confirmation_email(email, user.get('name', ''), token)
            except Exception as e:
                logger.warning("Resend confirmation failed for %s: %s", email, e)

        return {"success": True, "message": "If an account exists, a confirmation email has been sent."}

    @app.post("/api/v1/auth/forgot-password")
    def forgot_password(request: dict):
        """Send a password-reset email.

        Body: { "email": "<user email>" }
        Always returns success (prevents email enumeration).
        """
        from scoring_engine.auth_service import (
            normalize_email, get_user_by_email, generate_reset_token,
        )
        from scoring_engine.email_service import send_password_reset_email

        email = normalize_email(request.get('email'))
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        user = get_user_by_email(email)
        if user:
            try:
                token = generate_reset_token(email)
                send_password_reset_email(email, user.get('name', ''), token)
                logger.info("Password reset email sent to %s", email)
            except Exception as e:
                logger.warning("Reset email failed for %s: %s", email, e)

        # Always success — don't reveal whether an account exists
        return {"success": True, "message": "If an account exists, a password reset email has been sent."}

    @app.post("/api/v1/auth/reset-password")
    def reset_password(request: dict):
        """Reset the password using a token from the email link.

        Body: { "token": "<base64 token>", "new_password": "<new pw, min 6 chars>" }
        """
        from scoring_engine.auth_service import reset_password_with_token, verify_reset_token

        token = request.get('token')
        new_password = request.get('new_password')
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        if not new_password or len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Peek at the email for logging before consuming the token
        email = verify_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired reset link. Please request a new one.")

        ok = reset_password_with_token(token, new_password)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to reset password. Please try again.")

        logger.info("Password reset completed for: %s", email)
        return {"success": True}

    # -----------------------------------------------------------------
    # Payment Endpoints (Phase 2)
    # -----------------------------------------------------------------

    @app.post("/api/v1/payment/create-checkout")
    def create_checkout(
        assessment_id: str,
        customer_email: str,
        product: str = "COSMIC_BUNDLE",
        success_url: str = "http://localhost:3000/success",
        cancel_url: str = "http://localhost:3000/cancel",
    ):
        """Create Stripe checkout session for a single product unlock.

        `product` must be one of the SKUs defined in
        `scoring_engine.access_control.ALL_PRODUCTS`.
        """
        from scoring_engine.payment_service import create_checkout_session

        if product not in ALL_PRODUCTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product. Must be one of: {list(ALL_PRODUCTS)}",
            )

        session = create_checkout_session(
            assessment_id=assessment_id,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url,
            product=product,
        )

        if not session:
            raise HTTPException(status_code=500, detail="Failed to create checkout session")

        return {"success": True, "session": session}

    @app.post("/api/v1/payment/webhook")
    async def payment_webhook(request: Request):
        """Handle Stripe webhook events."""
        from scoring_engine.payment_service import (
            verify_webhook_signature,
            process_payment_webhook,
        )

        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        logger.info("Received Stripe webhook")

        if not verify_webhook_signature(payload, signature):
            logger.error("Webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")

        logger.info("Webhook signature verified")

        import json
        event_data = json.loads(payload)
        event_type = event_data.get('type', 'unknown')
        logger.info(f"Processing webhook event type: {event_type}")

        result = process_payment_webhook(event_data)

        if result:
            logger.info(f"Payment processed successfully: {result}")
            product = result.get("product", "COSMIC_BUNDLE")
            unlock_success = unlock_products(
                result['assessment_id'],
                [product],
                payment_id=result['payment_id'],
            )
            if unlock_success:
                logger.info(
                    f"✓ Unlocked '{product}' for assessment {result['assessment_id']}"
                )
            else:
                logger.error(
                    f"✗ Failed to unlock '{product}' for assessment {result['assessment_id']}"
                )
        else:
            logger.warning(
                f"No result from process_payment_webhook for event type: {event_type}"
            )

        return {"success": True}

    @app.get("/api/v1/payment/status/{assessment_id}")
    def get_payment_status_endpoint(assessment_id: str):
        """Get payment status for an assessment.

        Returns both the legacy single-string flag (for backwards
        compatibility) and the granular `paid_products` list.
        """
        from scoring_engine.payment_service import get_payment_status

        status = get_payment_status(assessment_id)
        paid_products = get_paid_products(assessment_id)
        return {
            "success": True,
            "payment_status": status,
            "paid_products": paid_products,
        }

    @app.post(
        "/api/v1/admin/mark-paid/{assessment_id}",
        dependencies=[Depends(require_admin)],
    )
    def admin_mark_paid(
        assessment_id: str,
        product: str = "COSMIC_BUNDLE",
        payment_id: str = "manual_admin_override",
    ):
        """Admin endpoint to manually unlock a product for an assessment.

        Requires `X-Admin-Token` header. Defaults to unlocking the full
        Cosmic bundle for backwards compatibility.
        """
        if product not in ALL_PRODUCTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product. Must be one of: {list(ALL_PRODUCTS)}",
            )

        logger.info(
            f"Admin marking assessment {assessment_id} as paid for product {product}"
        )
        success = unlock_products(assessment_id, [product], payment_id=payment_id)

        if success:
            return {
                "success": True,
                "message": f"Assessment {assessment_id} unlocked for {product}",
                "assessment_id": assessment_id,
                "product": product,
                "payment_id": payment_id,
                "paid_products": get_paid_products(assessment_id),
            }
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unlock {product} for assessment {assessment_id}",
        )

    @app.post("/api/v1/convert-to-scorecard")
    def convert_to_scorecard(full_result: dict):
        """Convert a full result to scorecard format."""
        try:
            from scoring_engine.output import build_scorecard_output
            scorecard_data = build_scorecard_output(full_result)
            return {"success": True, "data": scorecard_data}
        except Exception as e:
            logger.error(f"Failed to convert to scorecard: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    @app.get("/api/v1/user/{user_email}/reports")
    def get_user_reports(user_email: str):
        """Get all reports for a user (both free and paid)."""
        if not db_available:
            # Fallback to memory store
            user_reports = []
            for result_id, result_data in memory_store.items():
                metadata = result_data.get('metadata', {})
                if metadata.get('user_email') == user_email or metadata.get('user_id') == user_email:
                    user_reports.append({
                        'id': result_id,
                        'report_type': metadata.get('report_type', 'STUDENT_SUCCESS'),
                        'archetype_id': result_data.get('archetype', {}).get('archetype_id'),
                        'created_at': metadata.get('timestamp'),
                        'payment_status': 'free',  # Memory store doesn't track payments
                    })
            return {"success": True, "reports": user_reports}
        
        try:
            from scoring_engine.database import get_results_by_user

            # Get user_id from email (since database stores by user_id which is email)
            logger.info(f"Fetching reports for user_email: {user_email}")
            reports = get_results_by_user(user_email)
            logger.info(f"Found {len(reports)} reports from database")
            
            # Enrich with payment status (legacy single string + per-product map)
            enriched_reports = []
            for report in reports:
                rid = report['id']
                paid_products = get_paid_products(rid)
                payment_status = 'paid' if paid_products else 'free'

                enriched_reports.append({
                    **report,
                    'payment_status': payment_status,
                    'paid_products': paid_products,
                })
            
            logger.info(f"Returning {len(enriched_reports)} enriched reports")
            return {"success": True, "reports": enriched_reports}
            
        except Exception as e:
            logger.error(f"Failed to fetch user reports: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

    # -----------------------------------------------------------------
    # PDF Export Endpoints (Phase 2)
    # -----------------------------------------------------------------

    def _fetch_result(result_id: str) -> dict:
        """Fetch assessment result from database or memory store."""
        result_data = None
        
        if db_available:
            try:
                logger.info(f"Attempting database lookup for result_id: {result_id}")
                from scoring_engine.database import get_result_by_id
                result_data = get_result_by_id(result_id)
                if result_data:
                    logger.info(f"Result found in database for result_id: {result_id}")
                else:
                    logger.warning(f"Result not found in database for result_id: {result_id}")
            except Exception as e:
                logger.error(f"Database lookup failed for result_id {result_id}: {e}", exc_info=True)
        
        if not result_data:
            logger.info(f"Checking memory store for result_id: {result_id}")
            logger.debug(f"Memory store keys: {list(memory_store.keys())}")
            if result_id in memory_store:
                result_data = memory_store[result_id]
                logger.info(f"Result found in memory store for result_id: {result_id}")
            else:
                logger.warning(f"Result not found in memory store for result_id: {result_id}")
        
        if not result_data:
            logger.error(f"Result '{result_id}' not found in database or memory store")
            raise HTTPException(
                status_code=404, 
                detail=f"Result '{result_id}' not found. Available keys: {list(memory_store.keys())[:5]}"
            )
        
        return result_data

    def _verify_assessment_owner(result_data: dict, x_user_email: Optional[str], result_id: str) -> None:
        """Soft ownership check.

        If the caller supplies an X-User-Email header it MUST match the
        assessment's owner. When the header is absent we fall through (the
        free ScoreCard is intentionally shareable), but we log so abuse can
        be spotted in audit. This blocks trivial UUID-guessing attacks where
        the attacker has guessed an ID but isn't logged in as that user.
        """
        if not x_user_email:
            return
        owner = (
            (result_data or {}).get('metadata', {}).get('user_email')
            or (result_data or {}).get('metadata', {}).get('user_id')
        )
        if owner and owner.lower() != x_user_email.strip().lower():
            logger.warning(
                f"Owner mismatch on result {result_id}: caller={x_user_email}, owner={owner}"
            )
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this assessment.",
            )

    @app.get("/api/v1/export/scorecard-pdf/{result_id}")
    def export_scorecard_pdf(
        result_id: str,
        x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    ):
        """Generate and download FREE ScoreCard PDF (matches web ScoreCard view).

        The free ScoreCard is intentionally shareable. To block trivial
        ID-guessing attacks, callers MAY supply X-User-Email; if present it
        must match the assessment's owner.
        """
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_scorecard_pdf
        
        logger.info(f"ScoreCard PDF export requested for result_id: {result_id}")
        result_data = _fetch_result(result_id)
        _verify_assessment_owner(result_data, x_user_email, result_id)
        
        logger.info(f"Generating ScoreCard PDF for result_id: {result_id}")
        try:
            pdf_bytes = generate_scorecard_pdf(result_data)
            if pdf_bytes:
                logger.info(f"ScoreCard PDF generated: {len(pdf_bytes)} bytes")
            else:
                logger.error(f"ScoreCard PDF generation returned None for result_id: {result_id}")
        except Exception as e:
            logger.error(f"ScoreCard PDF generation failed for {result_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"ScoreCard PDF generation error: {str(e)}")
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate ScoreCard PDF")
        
        filename = f"BEST_Galaxy_ScoreCard_{result_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @app.get("/api/v1/export/pdf/{result_id}")
    def export_pdf(result_id: str, lens: Optional[str] = None):
        """Generate and download Full Report PDF (paid tier).

        Requires the requested lens (or any lens if `lens` is None) to be
        unlocked for this assessment.
        """
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_pdf_report

        logger.info(f"Full Report PDF export requested for result_id: {result_id}, lens: {lens}")
        result_data = _fetch_result(result_id)

        original_report_type = result_data.get('metadata', {}).get('report_type')
        report_type = lens if lens else original_report_type

        # Paywall: require the specific lens (or any lens if unspecified)
        if report_type and report_type in LENS_PRODUCTS:
            require_paid_product(result_id, report_type)
        elif report_type == "FULL_GALAXY":
            require_paid_product(result_id, "COSMIC_BUNDLE")
        else:
            require_any_paid(result_id, LENS_PRODUCTS + ("COSMIC_BUNDLE",))
        
        logger.info(f"Generating Full Report PDF for result_id: {result_id}, report_type: {report_type} (original: {original_report_type})")

        # Pull the lens-specific AI narrative if one has been generated for
        # this assessment. Without this overlay every lens PDF reuses the
        # lens-neutral baseline `interpretation` and looks the same.
        lens_sections = None
        if report_type and report_type != "FULL_GALAXY":
            try:
                from scoring_engine.report_generator import get_user_lens_reports
                user_id = (
                    result_data.get("metadata", {}).get("user_email")
                    or result_data.get("metadata", {}).get("user_id")
                )
                if user_id:
                    all_lens = get_user_lens_reports(user_id, result_id)
                    lens_sections = all_lens.get(report_type)
                    if lens_sections:
                        logger.info(f"Overlaying lens-specific narrative for {report_type} ({len(lens_sections)} sections)")
                    else:
                        logger.info(f"No lens-specific narrative stored for {report_type}; using baseline interpretation")
            except Exception as e:
                logger.warning(f"Lens narrative lookup failed for {report_type}: {e}")

        try:
            pdf_bytes = generate_pdf_report(result_data, lens_override=lens, lens_sections=lens_sections)
            if pdf_bytes:
                logger.info(f"Full Report PDF generated: {len(pdf_bytes)} bytes")
            else:
                logger.error(f"Full Report PDF generation returned None for result_id: {result_id}")
        except Exception as e:
            logger.error(f"Full Report PDF generation failed for {result_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate PDF - no bytes returned")
        
        # Distinct prefix `DataReport` so users can tell this apart from the
        # AI Narrative Report (which uses `AINarrative` prefix). Both share
        # the lens name, so without the prefix they collide in the
        # Downloads folder.
        lens_label = (lens or report_type or "").upper()
        lens_suffix = f"_{lens_label}" if lens_label else ""
        filename = f"BEST_Galaxy_DataReport{lens_suffix}_{result_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # -----------------------------------------------------------------
    # AI Report PDF Export
    # -----------------------------------------------------------------

    @app.get("/api/v1/export/ai-report-pdf/{report_id}")
    def export_ai_report_pdf(report_id: str):
        """Generate and download PDF for an AI-generated lens or Cosmic report.

        Requires the underlying lens (or COSMIC_BUNDLE for FULL_GALAXY) to be
        paid for the report's parent assessment.
        """
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_ai_report_pdf
        from scoring_engine.report_generator import get_report

        logger.info(f"AI report PDF export requested for report_id: {report_id}")

        report = get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"AI report '{report_id}' not found")

        sections = report.get("sections", {})
        report_type = report.get("report_type", "PERSONAL_LIFESTYLE")
        user_id = report.get("user_id")
        generated_at = report.get("generated_at")
        assessment_id = report.get("assessment_id")

        # Paywall on the parent assessment.
        if assessment_id:
            if report_type == "FULL_GALAXY":
                require_paid_product(assessment_id, "COSMIC_BUNDLE")
            elif report_type in LENS_PRODUCTS:
                require_paid_product(assessment_id, report_type)
            else:
                require_any_paid(
                    assessment_id, LENS_PRODUCTS + ("COSMIC_BUNDLE",)
                )

        pdf_bytes = generate_ai_report_pdf(
            report_sections=sections,
            report_type=report_type,
            user_id=user_id,
            generated_at=generated_at,
        )
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate AI report PDF")

        # Distinct prefix so AI narrative PDFs are clearly separable from
        # the Data Report PDFs (which use `DataReport` prefix). The cosmic
        # narrative gets its own short prefix to differentiate it from
        # the Cosmic Dashboard PDF.
        if report_type == "FULL_GALAXY":
            filename = f"BEST_Cosmic_Narrative_{report_id[:8]}.pdf"
        else:
            lens_label = report_type.upper()
            filename = f"BEST_Galaxy_AINarrative_{lens_label}_{report_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # -----------------------------------------------------------------
    # Legal Consent Endpoint
    # -----------------------------------------------------------------

    @app.post("/api/v1/consent")
    def record_consent(request: dict):
        """Record a user's pre-assessment legal consent.

        Stores an audit row with: user_id, the legal version they
        acknowledged, which checkboxes they ticked, IP/user-agent (when
        available), and a server-side timestamp.  Used as evidence that
        the user agreed to the Terms / Disclaimer / Data-Use clauses
        before starting the assessment.

        Body:
          - user_id: optional (email or id; null for anonymous gating)
          - legal_version: required (e.g. "2026-04-30")
          - consents: required dict (e.g. {"terms": true, "responsibility": true,
            "research": false})
          - user_agent: optional
        """
        from datetime import datetime, timezone

        legal_version = request.get("legal_version")
        consents = request.get("consents") or {}
        if not legal_version or not isinstance(consents, dict):
            raise HTTPException(
                status_code=400,
                detail="legal_version and consents are required",
            )

        # Required-checkbox enforcement at the API boundary.  The frontend
        # also blocks submission, but a malicious client could bypass that.
        if not (consents.get("terms") and consents.get("responsibility")):
            raise HTTPException(
                status_code=400,
                detail="Required consents (terms, responsibility) must be true",
            )

        record = {
            "user_id": request.get("user_id"),
            "legal_version": legal_version,
            "consents": consents,
            "user_agent": request.get("user_agent"),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        # Persist if Supabase is available; otherwise just log so the
        # consent is at least captured in container logs.
        record_id = None
        if db_available:
            try:
                from scoring_engine.supabase_client import get_supabase_client
                client = get_supabase_client()
                if client is not None:
                    res = (
                        client.table("legal_consents")
                        .insert(record)
                        .execute()
                    )
                    if res.data:
                        record_id = res.data[0].get("id")
            except Exception as e:
                # Don't bubble up — the user has already provided consent
                # client-side and shouldn't be blocked by a logging hiccup.
                logger.warning("Consent log DB write failed: %s", e)

        logger.info(
            "Consent recorded: user=%s version=%s consents=%s",
            record.get("user_id"), legal_version, consents,
        )
        return {"success": True, "record_id": record_id, "recorded_at": record["recorded_at"]}

    # -----------------------------------------------------------------
    # Demographics Intake Endpoints
    # -----------------------------------------------------------------

    @app.get("/api/v1/demographics/questions")
    def get_demographic_questions():
        """Return the demographic intake survey questions for the frontend."""
        from scoring_engine.demographics import DEMOGRAPHIC_QUESTIONS
        return {"success": True, "questions": DEMOGRAPHIC_QUESTIONS}

    @app.post("/api/v1/demographics/submit")
    def submit_demographics(request: dict):
        """Submit demographic intake responses."""
        from scoring_engine.demographics import (
            build_demographic_output,
            store_demographics,
        )

        user_id = request.get("user_id")
        assessment_id = request.get("assessment_id")
        raw_responses = request.get("responses", {})

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        demographics = build_demographic_output(raw_responses)

        # Store in DB if available
        record_id = None
        if db_available:
            record_id = store_demographics(user_id, assessment_id or "", demographics)

        # Also store in memory for immediate access
        memory_store[f"demo_{user_id}_{assessment_id or 'latest'}"] = demographics

        return {
            "success": True,
            "record_id": record_id,
            "demographics": demographics,
        }

    @app.get("/api/v1/demographics/{user_id}")
    def get_user_demographics(user_id: str, assessment_id: Optional[str] = None):
        """Retrieve stored demographics for a user."""
        from scoring_engine.demographics import get_demographics

        # Try DB
        if db_available:
            data = get_demographics(user_id, assessment_id)
            if data:
                return {"success": True, "demographics": data}

        # Fallback to memory
        key = f"demo_{user_id}_{assessment_id or 'latest'}"
        if key in memory_store:
            return {"success": True, "demographics": memory_store[key]}

        return {"success": True, "demographics": None}

    # -----------------------------------------------------------------
    # AI Report Generation Endpoints
    # -----------------------------------------------------------------

    @app.post("/api/v1/reports/generate")
    def generate_lens_report(request: dict):
        """
        Generate an AI-powered report for a specific lens.

        Required:
          - assessment_id: ID of the completed assessment
          - report_type: one of STUDENT_SUCCESS, PERSONAL_LIFESTYLE,
                         PROFESSIONAL_LEADERSHIP, FAMILY_ECOSYSTEM
        Optional:
          - demographics: demographic context dict (or auto-fetched from storage)
        """
        from scoring_engine.report_generator import generate_report, store_report

        assessment_id = request.get("assessment_id")
        report_type = request.get("report_type")
        demographics = request.get("demographics")
        request_user_id = request.get("user_id")

        if not assessment_id or not report_type:
            raise HTTPException(
                status_code=400,
                detail="assessment_id and report_type are required",
            )

        valid_types = [
            "STUDENT_SUCCESS", "PERSONAL_LIFESTYLE",
            "PROFESSIONAL_LEADERSHIP", "FAMILY_ECOSYSTEM",
        ]
        if report_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"report_type must be one of: {valid_types}",
            )

        # Paywall: require this lens (or the cosmic bundle, which includes it).
        require_paid_product(assessment_id, report_type)

        # Fetch assessment data
        assessment_data = _fetch_result(assessment_id)

        # Resolve user_id from request or assessment metadata
        meta = assessment_data.get("metadata", {})
        user_id = request_user_id or meta.get("user_email") or meta.get("user_id", "")

        # Auto-fetch demographics if not provided — try multiple lookup keys
        if not demographics:
            lookup_ids = list(dict.fromkeys(filter(None, [
                user_id, meta.get("user_email"), meta.get("user_id"),
            ])))
            for uid in lookup_ids:
                demo_key = f"demo_{uid}_{assessment_id}"
                if demo_key in memory_store:
                    demographics = memory_store[demo_key]
                    break
                demo_key_latest = f"demo_{uid}_latest"
                if demo_key_latest in memory_store:
                    demographics = memory_store[demo_key_latest]
                    break
            if not demographics and db_available:
                from scoring_engine.demographics import get_demographics
                for uid in lookup_ids:
                    demographics = get_demographics(uid, assessment_id)
                    if demographics:
                        break

        # Generate report
        try:
            report = generate_report(assessment_data, report_type, demographics)
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

        # Store report
        report_id = store_report(user_id or "unknown", assessment_id, report)

        return {
            "success": True,
            "report_id": report_id,
            "report": report,
        }

    @app.get("/api/v1/reports/{report_id}")
    def get_generated_report(report_id: str):
        """Retrieve a generated AI report by ID.

        Returns full sections only if the parent assessment has paid for the
        relevant SKU. Otherwise returns metadata + a 'locked' flag so the
        frontend can render a blurred preview.
        """
        from scoring_engine.report_generator import get_report

        report = get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

        report_type = report.get("report_type", "")
        assessment_id = report.get("assessment_id")

        required_product = (
            "COSMIC_BUNDLE" if report_type == "FULL_GALAXY"
            else report_type if report_type in LENS_PRODUCTS
            else None
        )

        if required_product and assessment_id and not is_product_paid(
            assessment_id, required_product
        ):
            return {
                "success": True,
                "locked": True,
                "report": {
                    "report_id": report.get("report_id"),
                    "report_type": report_type,
                    "user_id": report.get("user_id"),
                    "assessment_id": assessment_id,
                    "generated_at": report.get("generated_at"),
                    "required_product": required_product,
                },
            }

        return {"success": True, "locked": False, "report": report}

    @app.get("/api/v1/reports/user/{user_id}/assessment/{assessment_id}")
    def get_user_assessment_reports(user_id: str, assessment_id: str):
        """Get all generated reports for a user's assessment.

        Sections are only returned for SKUs that have been paid; locked lenses
        are surfaced as `{ <LENS>: null }` so the frontend can render a teaser.
        """
        from scoring_engine.report_generator import (
            get_user_lens_reports,
            get_user_lens_report_ids,
        )

        reports = get_user_lens_reports(user_id, assessment_id)
        report_ids = get_user_lens_report_ids(user_id, assessment_id)
        paid_products = get_paid_products(assessment_id)

        gated_reports: dict = {}
        for lens, sections in reports.items():
            required = (
                "COSMIC_BUNDLE" if lens == "FULL_GALAXY"
                else lens if lens in LENS_PRODUCTS
                else None
            )
            if required and required not in paid_products and \
                    not (lens in LENS_PRODUCTS and "COSMIC_BUNDLE" in paid_products):
                gated_reports[lens] = None
            else:
                gated_reports[lens] = sections

        return {
            "success": True,
            "reports": gated_reports,
            "report_ids": report_ids,
            "paid_products": paid_products,
            "lens_count": sum(1 for v in gated_reports.values() if v),
        }

    # -----------------------------------------------------------------
    # Cosmic Integration Report Endpoints
    # -----------------------------------------------------------------

    @app.get("/api/v1/cosmic/eligibility/{user_id}/{assessment_id}")
    def check_cosmic_eligibility_endpoint(user_id: str, assessment_id: str):
        """Check if user can unlock the Cosmic Integration Report.

        Two requirements:
          1. Generation requirement: all 4 lens reports must already exist.
          2. Payment requirement: the COSMIC_BUNDLE SKU must be paid OR all
             4 lens SKUs must be paid individually.
        """
        from scoring_engine.report_generator import check_cosmic_eligibility

        gen = check_cosmic_eligibility(user_id, assessment_id)

        paid_products = get_paid_products(assessment_id)
        cosmic_paid = "COSMIC_BUNDLE" in paid_products
        all_lenses_paid = all(p in paid_products for p in LENS_PRODUCTS)
        payment_eligible = cosmic_paid or all_lenses_paid

        return {
            "success": True,
            **gen,
            "payment_eligible": payment_eligible,
            "paid_products": paid_products,
            "eligible": gen["eligible"] and payment_eligible,
            "generation_eligible": gen["eligible"],
            "message": (
                "Cosmic Integration unlocked."
                if gen["eligible"] and payment_eligible
                else "Generate all 4 lens reports and purchase the Cosmic bundle."
                if not gen["eligible"] and not payment_eligible
                else "Generate all 4 lens reports first."
                if not gen["eligible"]
                else "Purchase the Cosmic bundle to unlock the integration report."
            ),
        }

    @app.get("/api/v1/cosmic/report/{user_id}/{assessment_id}")
    def get_cosmic_report(user_id: str, assessment_id: str):
        """Retrieve a previously generated FULL_GALAXY (cosmic) report."""
        require_paid_product(assessment_id, "COSMIC_BUNDLE")
        # Strip leftover `**` markdown markers from reports persisted by an
        # older version of the section flattener — keeps prior cosmic
        # generations readable without forcing a paid regenerate.
        from scoring_engine.report_generator import _sanitize_stored_sections

        try:
            from scoring_engine.supabase_client import get_supabase_client
            client = get_supabase_client()
            if client is not None:
                response = (
                    client.table("generated_reports")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("assessment_id", assessment_id)
                    .eq("report_type", "FULL_GALAXY")
                    .order("generated_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if response.data:
                    return _sanitize_stored_sections(response.data[0])
        except Exception as e:
            logger.debug(f"Cosmic report DB lookup failed: {e}")

        # Fallback to in-memory store
        from scoring_engine.report_generator import _report_store
        for rid, rdata in _report_store.items():
            if (rdata.get("user_id") == user_id
                    and rdata.get("assessment_id") == assessment_id
                    and rdata.get("report_type") == "FULL_GALAXY"):
                return _sanitize_stored_sections(rdata)

        raise HTTPException(status_code=404, detail="No cosmic report found for this assessment")

    @app.post("/api/v1/cosmic/generate")
    def generate_cosmic_report_endpoint(request: dict):
        """
        Generate the Cosmic Integration Report.
        Requires all 4 lens reports to be already generated.
        """
        from scoring_engine.report_generator import (
            check_cosmic_eligibility,
            get_user_lens_reports,
            generate_cosmic_report,
            store_report,
        )

        assessment_id = request.get("assessment_id")
        user_id = request.get("user_id")
        demographics = request.get("demographics")

        if not assessment_id or not user_id:
            raise HTTPException(
                status_code=400,
                detail="assessment_id and user_id are required",
            )

        # Paywall: Cosmic synthesis requires the COSMIC_BUNDLE SKU.
        require_paid_product(assessment_id, "COSMIC_BUNDLE")

        # Generation eligibility: all 4 lens reports must exist.
        eligibility = check_cosmic_eligibility(user_id, assessment_id)
        if not eligibility["eligible"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cosmic Integration requires all 4 lens reports to be "
                    f"generated first. Missing: {eligibility['missing_lenses']}"
                ),
            )

        # Fetch assessment data
        assessment_data = _fetch_result(assessment_id)

        # Get all 4 lens reports
        lens_reports = get_user_lens_reports(user_id, assessment_id)

        # Auto-fetch demographics if not provided — try multiple lookup keys
        if not demographics:
            meta = assessment_data.get("metadata", {})
            lookup_ids = list(dict.fromkeys(filter(None, [
                user_id, meta.get("user_email"), meta.get("user_id"),
            ])))
            for uid in lookup_ids:
                demo_key = f"demo_{uid}_{assessment_id}"
                if demo_key in memory_store:
                    demographics = memory_store[demo_key]
                    break
                demo_key_latest = f"demo_{uid}_latest"
                if demo_key_latest in memory_store:
                    demographics = memory_store[demo_key_latest]
                    break
            if not demographics and db_available:
                from scoring_engine.demographics import get_demographics
                for uid in lookup_ids:
                    demographics = get_demographics(uid, assessment_id)
                    if demographics:
                        break

        # Generate cosmic report
        try:
            report = generate_cosmic_report(lens_reports, assessment_data, demographics)
        except Exception as e:
            logger.error(f"Cosmic report generation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Cosmic report generation failed: {str(e)}")

        # Store
        report_id = store_report(user_id, assessment_id, report)

        return {
            "success": True,
            "report_id": report_id,
            "report": report,
        }

    # -----------------------------------------------------------------
    # Deep-Dive Reports (Financial / Health)
    # -----------------------------------------------------------------

    def _resolve_demographics(user_id: str, assessment_id: str, meta: dict, provided: Optional[dict]) -> Optional[dict]:
        """Shared demographic-lookup logic used by deep-dive and compatibility."""
        if provided:
            return provided
        lookup_ids = list(dict.fromkeys(filter(None, [
            user_id, meta.get("user_email"), meta.get("user_id"),
        ])))
        for uid in lookup_ids:
            for key in (f"demo_{uid}_{assessment_id}", f"demo_{uid}_latest"):
                if key in memory_store:
                    return memory_store[key]
        if db_available:
            from scoring_engine.demographics import get_demographics
            for uid in lookup_ids:
                d = get_demographics(uid, assessment_id)
                if d:
                    return d
        return None

    @app.post("/api/v1/reports/deep-dive/financial")
    def generate_financial_deep_dive_endpoint(request: dict):
        """Generate a Financial Executive Functioning deep-dive report."""
        from scoring_engine.deep_dive import generate_financial_deep_dive
        from scoring_engine.report_generator import store_report

        assessment_id = request.get("assessment_id")
        user_id = request.get("user_id")
        if not assessment_id or not user_id:
            raise HTTPException(status_code=400, detail="assessment_id and user_id are required")

        require_paid_product(assessment_id, "FINANCIAL_DEEP_DIVE")

        assessment_data = _fetch_result(assessment_id)
        meta = assessment_data.get("metadata", {})
        demographics = _resolve_demographics(user_id, assessment_id, meta, request.get("demographics"))

        try:
            report = generate_financial_deep_dive(
                assessment_data, demographics,
                user_id=user_id, assessment_id=assessment_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Financial deep-dive failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

        report_id = store_report(user_id, assessment_id, report)
        return {"success": True, "report_id": report_id, "report": report}

    @app.post("/api/v1/reports/deep-dive/health")
    def generate_health_deep_dive_endpoint(request: dict):
        """Generate a Health & Fitness Executive Functioning deep-dive report."""
        from scoring_engine.deep_dive import generate_health_deep_dive
        from scoring_engine.report_generator import store_report

        assessment_id = request.get("assessment_id")
        user_id = request.get("user_id")
        if not assessment_id or not user_id:
            raise HTTPException(status_code=400, detail="assessment_id and user_id are required")

        require_paid_product(assessment_id, "HEALTH_DEEP_DIVE")

        assessment_data = _fetch_result(assessment_id)
        meta = assessment_data.get("metadata", {})
        demographics = _resolve_demographics(user_id, assessment_id, meta, request.get("demographics"))

        try:
            report = generate_health_deep_dive(
                assessment_data, demographics,
                user_id=user_id, assessment_id=assessment_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Health deep-dive failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

        report_id = store_report(user_id, assessment_id, report)
        return {"success": True, "report_id": report_id, "report": report}

    # -----------------------------------------------------------------
    # Compatibility Report
    # -----------------------------------------------------------------

    @app.post("/api/v1/reports/compatibility")
    def generate_compatibility_endpoint(request: dict):
        """
        Generate a structural compatibility report between two completed assessments.

        Required:
          - assessment_a_id, assessment_b_id
        Optional:
          - user_a_id, user_b_id (for audit/storage)
        """
        from scoring_engine.compatibility import generate_compatibility_report

        a_id = request.get("assessment_a_id")
        b_id = request.get("assessment_b_id")
        if not a_id or not b_id:
            raise HTTPException(
                status_code=400,
                detail="assessment_a_id and assessment_b_id are required",
            )

        # Either side having paid for COMPATIBILITY unlocks the joint report.
        if not (
            is_product_paid(a_id, "COMPATIBILITY")
            or is_product_paid(b_id, "COMPATIBILITY")
        ):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "payment_required",
                    "product": "COMPATIBILITY",
                    "message": (
                        "Compatibility Report requires the COMPATIBILITY "
                        "unlock on at least one of the two assessments."
                    ),
                },
            )

        try:
            assessment_a = _fetch_result(a_id)
            assessment_b = _fetch_result(b_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch assessments: {e}")

        try:
            report = generate_compatibility_report(
                assessment_a, assessment_b,
                user_a_id=request.get("user_a_id"),
                user_b_id=request.get("user_b_id"),
            )
        except Exception as e:
            logger.error(f"Compatibility generation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

        # Store under user_a_id / assessment_a_id for traceability
        from scoring_engine.report_generator import store_report
        report_id = store_report(
            request.get("user_a_id") or "compat",
            a_id,
            report,
        )
        return {"success": True, "report_id": report_id, "report": report}

    # -----------------------------------------------------------------
    # Cosmic Dashboard PDF Export
    # -----------------------------------------------------------------

    @app.get("/api/v1/export/cosmic-dashboard-pdf/{user_id}/{assessment_id}")
    def export_cosmic_dashboard_pdf(user_id: str, assessment_id: str):
        """
        Export the cosmic dashboard (visuals + narrative) as a PDF.
        Falls back to the standard AI-report PDF if no cosmic report exists.
        """
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_cosmic_dashboard_pdf

        require_paid_product(assessment_id, "COSMIC_BUNDLE")

        try:
            assessment_data = _fetch_result(assessment_id)
        except HTTPException:
            raise

        # Find the most recent cosmic report (if any)
        cosmic_report = None
        try:
            from scoring_engine.supabase_client import get_supabase_client
            client = get_supabase_client()
            if client is not None:
                response = (
                    client.table("generated_reports")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("assessment_id", assessment_id)
                    .eq("report_type", "FULL_GALAXY")
                    .order("generated_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if response.data:
                    cosmic_report = response.data[0]
        except Exception as e:
            logger.debug(f"Cosmic PDF — DB lookup failed: {e}")

        if cosmic_report is None:
            from scoring_engine.report_generator import _report_store
            for rdata in _report_store.values():
                if (rdata.get("user_id") == user_id
                        and rdata.get("assessment_id") == assessment_id
                        and rdata.get("report_type") == "FULL_GALAXY"):
                    cosmic_report = rdata
                    break

        try:
            pdf_bytes = generate_cosmic_dashboard_pdf(
                assessment_data=assessment_data,
                cosmic_report=cosmic_report,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Cosmic dashboard PDF generation failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="PDF generation failed")

        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate cosmic dashboard PDF")

        # Date-stamped filename without IDs — matches the rest of the
        # download set (DataReport / AINarrative / ScoreCard / Cosmic
        # Narrative) and gives the user a clean, shareable filename.
        from datetime import date as _date
        filename = f"BEST_Cosmic_Dashboard_{_date.today().isoformat()}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # -----------------------------------------------------------------
    # AI Audit Log Endpoints
    # -----------------------------------------------------------------

    @app.get(
        "/api/v1/audit/logs",
        dependencies=[Depends(require_admin)],
    )
    def list_audit_logs(
        user_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        limit: int = 50,
    ):
        """List recent AI prompt/response audit log entries (admin only)."""
        from scoring_engine import audit
        return {
            "success": True,
            "logs": audit.get_audit_logs(
                user_id=user_id,
                assessment_id=assessment_id,
                limit=min(max(limit, 1), 500),
            ),
        }

    @app.get(
        "/api/v1/audit/summary",
        dependencies=[Depends(require_admin)],
    )
    def audit_summary():
        """Aggregate stats over the in-memory audit buffer (admin only)."""
        from scoring_engine import audit
        return {"success": True, "summary": audit.get_audit_summary()}

    return app


# Default app instance with database enabled
app = create_app(use_database=True)
