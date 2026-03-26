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

from fastapi import FastAPI, HTTPException, Depends
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
    report_type: str = Field(..., description="Report lens (e.g. STUDENT_SUCCESS)")
    responses: list[ResponseItem] = Field(..., min_length=1, description="Assessment responses")
    demographics: Optional[dict] = Field(None, description="Optional demographic metadata")
    include_interpretation: bool = Field(True, description="Include AI narrative layer")
    tier: str = Field("free", description="Output tier: 'free' (ScoreCard) or 'paid' (Full Report)")


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

    return app


# Default app instance (no database — for development/testing)
app = create_app(use_database=False)
