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
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    """Assessment submission payload."""
    user_id: str = Field(..., description="Unique user identifier")
    user_email: Optional[str] = Field(None, description="User email address")
    report_type: str = Field(..., description="Report lens (e.g. STUDENT_SUCCESS)")
    responses: list[ResponseItem] = Field(..., min_length=1, description="Assessment responses")
    demographics: Optional[dict] = Field(None, description="Optional demographic metadata")
    include_interpretation: bool = Field(True, description="Include AI narrative layer")
    tier: str = Field("free", description="Output tier: 'free' (ScoreCard) or 'paid' (Full Report)")
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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

        # Return appropriate tier output
        if request.tier == "free":
            from scoring_engine.output import build_scorecard_output
            response_data = build_scorecard_output(result)
        else:
            response_data = result

        return AssessmentResponse(
            success=True,
            result_id=result_id,
            data=response_data,
        )

    @app.get("/api/v1/results/{result_id}")
    def get_result(result_id: str):
        """Retrieve a stored assessment result by ID."""
        # Try Supabase first
        if db_available:
            try:
                from scoring_engine.database import get_result_by_id
                data = get_result_by_id(result_id)
                if data is not None:
                    return {"success": True, "data": data}
            except Exception as e:
                logger.error(f"Supabase lookup failed: {e}")

        # Fallback to memory store
        if result_id in memory_store:
            return {"success": True, "data": memory_store[result_id]}

        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")

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
        from scoring_engine.auth_service import create_user
        
        email = request.get('email')
        password = request.get('password')
        name = request.get('name')
        demographics = request.get('demographics')
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        user = create_user(email, password, name, demographics)
        
        if not user:
            raise HTTPException(status_code=400, detail="User already exists or creation failed")
        
        logger.info(f"New user signed up: {email}")
        return {"success": True, "user": user}

    @app.post("/api/v1/auth/login")
    def login(request: dict):
        """Authenticate a user and return session token."""
        from scoring_engine.auth_service import authenticate_user
        
        email = request.get('email')
        password = request.get('password')
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        user = authenticate_user(email, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"User logged in: {email}")
        return {"success": True, "user": user}

    @app.get("/api/v1/auth/user/{email}")
    def get_user(email: str):
        """Get user information by email."""
        from scoring_engine.auth_service import get_user_by_email
        
        user = get_user_by_email(email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "user": user}

    # -----------------------------------------------------------------
    # Payment Endpoints (Phase 2)
    # -----------------------------------------------------------------

    @app.post("/api/v1/payment/create-checkout")
    def create_checkout(
        assessment_id: str,
        customer_email: str,
        success_url: str = "http://localhost:3000/success",
        cancel_url: str = "http://localhost:3000/cancel"
    ):
        """Create Stripe checkout session for report unlock."""
        from scoring_engine.payment_service import create_checkout_session
        
        session = create_checkout_session(
            assessment_id=assessment_id,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url
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
            unlock_report
        )
        
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        logger.info("Received Stripe webhook")
        
        # Verify signature
        if not verify_webhook_signature(payload, signature):
            logger.error("Webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        logger.info("Webhook signature verified")
        
        # Parse event
        import json
        event_data = json.loads(payload)
        event_type = event_data.get('type', 'unknown')
        logger.info(f"Processing webhook event type: {event_type}")
        
        # Process payment
        result = process_payment_webhook(event_data)
        
        if result:
            logger.info(f"Payment processed successfully: {result}")
            # Unlock report
            unlock_success = unlock_report(result['assessment_id'], result['payment_id'])
            if unlock_success:
                logger.info(f"✓ Report successfully unlocked for assessment {result['assessment_id']}")
            else:
                logger.error(f"✗ Failed to unlock report for assessment {result['assessment_id']}")
        else:
            logger.warning(f"No result from process_payment_webhook for event type: {event_type}")
        
        return {"success": True}

    @app.get("/api/v1/payment/status/{assessment_id}")
    def get_payment_status_endpoint(assessment_id: str):
        """Get payment status for an assessment."""
        from scoring_engine.payment_service import get_payment_status
        
        status = get_payment_status(assessment_id)
        return {"success": True, "payment_status": status}

    @app.post("/api/v1/admin/mark-paid/{assessment_id}")
    def admin_mark_paid(assessment_id: str, payment_id: str = "manual_admin_override"):
        """Admin endpoint to manually mark a report as paid."""
        from scoring_engine.payment_service import unlock_report
        
        logger.info(f"Admin manually marking assessment {assessment_id} as paid")
        success = unlock_report(assessment_id, payment_id)
        
        if success:
            return {
                "success": True, 
                "message": f"Assessment {assessment_id} marked as paid",
                "assessment_id": assessment_id,
                "payment_id": payment_id
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to mark assessment {assessment_id} as paid"
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
            from scoring_engine.supabase_client import get_supabase_client
            
            # Get user_id from email (since database stores by user_id which is email)
            reports = get_results_by_user(user_email)
            
            # Enrich with payment status
            supabase = get_supabase_client()
            enriched_reports = []
            for report in reports:
                # Fetch payment status
                payment_result = supabase.table('assessment_results')\
                    .select('payment_status, user_id')\
                    .eq('id', report['id'])\
                    .maybe_single()\
                    .execute()
                
                payment_status = 'free'
                if payment_result.data:
                    payment_status = payment_result.data.get('payment_status', 'free')
                
                enriched_reports.append({
                    **report,
                    'payment_status': payment_status
                })
            
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

    @app.get("/api/v1/export/scorecard-pdf/{result_id}")
    def export_scorecard_pdf(result_id: str):
        """Generate and download FREE ScoreCard PDF (matches web ScoreCard view)."""
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_scorecard_pdf
        
        logger.info(f"ScoreCard PDF export requested for result_id: {result_id}")
        result_data = _fetch_result(result_id)
        
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
    def export_pdf(result_id: str):
        """Generate and download Full Report PDF (paid tier)."""
        from fastapi.responses import Response
        from scoring_engine.pdf_service import generate_pdf_report
        
        logger.info(f"Full Report PDF export requested for result_id: {result_id}")
        result_data = _fetch_result(result_id)
        
        logger.info(f"Generating Full Report PDF for result_id: {result_id}, report_type: {result_data.get('metadata', {}).get('report_type')}")
        try:
            pdf_bytes = generate_pdf_report(result_data)
            if pdf_bytes:
                logger.info(f"Full Report PDF generated: {len(pdf_bytes)} bytes")
            else:
                logger.error(f"Full Report PDF generation returned None for result_id: {result_id}")
        except Exception as e:
            logger.error(f"Full Report PDF generation failed for {result_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
        
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate PDF - no bytes returned")
        
        filename = f"BEST_Galaxy_Report_{result_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return app


# Default app instance (no database — for development/testing)
app = create_app(use_database=False)
