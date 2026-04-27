"""
Tests for the FastAPI REST API Layer (G2).
Uses FastAPI TestClient (in-memory, no database required).
"""

import pytest
from fastapi.testclient import TestClient
from scoring_engine.api import create_app
from scoring_engine.item_dictionary import ITEM_DICTIONARY
from scoring_engine.config import REPORT_LENSES


@pytest.fixture
def client():
    """Create a test client with no database (in-memory mode)."""
    app = create_app(use_database=False)
    return TestClient(app)


def _make_response_payload(value=3, report_type="STUDENT_SUCCESS"):
    """Build a valid assessment request payload."""
    return {
        "user_id": "test_api_user",
        "report_type": report_type,
        "responses": [
            {"item_id": item["item_id"], "response": value}
            for item in ITEM_DICTIONARY
        ],
        "demographics": {"age": 22, "role": "student"},
        "include_interpretation": True,
    }


def _submit_and_unlock(client, monkeypatch, payload, products=("STUDENT_SUCCESS",)):
    """Submit an assessment and simulate a paid unlock for the given SKUs.

    Returns the full paid result via GET /api/v1/results/{id}. Used by tests
    that need to verify the full-output shape (interpretation, archetype,
    construct_scores, etc.) — these are gated behind the paywall now that
    the client-controlled `tier` field has been removed.
    """
    submit_resp = client.post("/api/v1/assess", json=payload)
    assert submit_resp.status_code == 200, submit_resp.text
    result_id = submit_resp.json()["result_id"]

    paid_map = {result_id: list(products)}
    fake = lambda aid: paid_map.get(aid, [])
    # Patch BOTH the source module and the api.py-level rebind, since
    # api.py imports get_paid_products by name at import time.
    import scoring_engine.access_control as ac_mod
    import scoring_engine.api as api_mod
    monkeypatch.setattr(ac_mod, "get_paid_products", fake)
    monkeypatch.setattr(api_mod, "get_paid_products", fake)

    get_resp = client.get(f"/api/v1/results/{result_id}")
    assert get_resp.status_code == 200, get_resp.text
    body = get_resp.json()
    assert body["tier"] == "paid", body
    return body["data"], result_id


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "system_id" in data
        assert "system_name" in data


class TestAssessEndpoint:
    """POST /api/v1/assess"""

    def test_submit_valid_assessment(self, client, monkeypatch):
        """Full 52-item submission, after unlock, should return full output."""
        payload = _make_response_payload(3)
        data, _ = _submit_and_unlock(client, monkeypatch, payload)
        assert "metadata" in data
        assert "construct_scores" in data
        assert "load_framework" in data
        assert "domains" in data
        assert "summary" in data
        assert "items" in data
        assert "archetype" in data
        assert "interpretation" in data

    def test_submit_returns_correct_lens(self, client):
        """Report type should match what was requested."""
        payload = _make_response_payload(3, "PROFESSIONAL_LEADERSHIP")
        resp = client.post("/api/v1/assess", json=payload)
        data = resp.json()["data"]
        assert data["metadata"]["report_type"] == "PROFESSIONAL_LEADERSHIP"

    def test_submit_invalid_report_type(self, client):
        """Invalid report_type should return 400."""
        payload = _make_response_payload(3)
        payload["report_type"] = "INVALID_LENS"
        resp = client.post("/api/v1/assess", json=payload)
        assert resp.status_code == 400

    def test_submit_empty_responses(self, client):
        """Empty responses should return 422."""
        payload = {
            "user_id": "test",
            "report_type": "STUDENT_SUCCESS",
            "responses": [],
        }
        resp = client.post("/api/v1/assess", json=payload)
        assert resp.status_code == 422

    def test_submit_out_of_range_response(self, client):
        """Response value outside range should be handled gracefully."""
        payload = {
            "user_id": "test",
            "report_type": "STUDENT_SUCCESS",
            "responses": [{"item_id": "Q01", "response": 99}],
        }
        resp = client.post("/api/v1/assess", json=payload)
        # Pydantic validation catches ge=1, le=7
        assert resp.status_code == 422

    def test_submit_without_interpretation(self, client, monkeypatch):
        """Should work without interpretation layer (paid path)."""
        payload = _make_response_payload(3)
        payload["include_interpretation"] = False
        data, _ = _submit_and_unlock(client, monkeypatch, payload)
        assert "interpretation" not in data

    def test_demographics_passthrough(self, client):
        """Demographics should appear in metadata."""
        payload = _make_response_payload(3)
        payload["demographics"] = {"age": 30, "role": "teacher"}
        resp = client.post("/api/v1/assess", json=payload)
        data = resp.json()["data"]
        assert data["metadata"]["demographics"]["role"] == "teacher"

    def test_all_four_lenses(self, client):
        """All 4 report lenses should work."""
        for lens in REPORT_LENSES:
            payload = _make_response_payload(3, lens)
            resp = client.post("/api/v1/assess", json=payload)
            assert resp.status_code == 200, f"Failed for lens: {lens}"

    def test_construct_scores_have_both_methods(self, client, monkeypatch):
        """Paid output should include canonical (per-item) and domain-matrix indices."""
        payload = _make_response_payload(3)
        data, _ = _submit_and_unlock(client, monkeypatch, payload)
        cs = data["construct_scores"]
        # Canonical: simple per-item average over PEI / BHP behavioral items
        assert "PEI_score" in cs
        assert "BHP_score" in cs
        # Diagnostic: alternative roll-up via overlapping domain-weight matrix
        assert "PEI_score_by_domain_matrix" in cs
        assert "BHP_score_by_domain_matrix" in cs

    def test_archetype_assigned(self, client, monkeypatch):
        """Archetype should be present in paid output."""
        payload = _make_response_payload(3)
        data, _ = _submit_and_unlock(client, monkeypatch, payload)
        arch = data["archetype"]
        assert "archetype_id" in arch
        assert "description" in arch
        assert "confidence" in arch

    def test_free_tier_returns_scorecard(self, client):
        """Free tier should return ScoreCard output."""
        payload = _make_response_payload(3)
        payload["tier"] = "free"
        resp = client.post("/api/v1/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tier"] == "free"
        assert "galaxy_snapshot" in data
        assert "constellation" in data
        assert "load_balance" in data
        assert "strengths" in data
        assert "growth_edges" in data
        assert "lens_teasers" in data
        assert "locked_features" in data
        # Should NOT have full details
        assert "items" not in data
        assert "interpretation" not in data
        assert "domains" not in data

    def test_free_tier_has_4_constellation_groups(self, client):
        """Free ScoreCard should have exactly 4 constellation groups."""
        payload = _make_response_payload(3)
        payload["tier"] = "free"
        resp = client.post("/api/v1/assess", json=payload)
        data = resp.json()["data"]
        assert len(data["constellation"]) == 4
        names = [g["name"] for g in data["constellation"]]
        assert "Executive Function Skills" in names
        assert "Cognitive Control" in names
        assert "Emotional Regulation" in names
        assert "Environmental Demands" in names

    def test_free_tier_has_4_lens_teasers(self, client):
        """Free ScoreCard should have all 4 lens teasers."""
        payload = _make_response_payload(3)
        payload["tier"] = "free"
        resp = client.post("/api/v1/assess", json=payload)
        teasers = resp.json()["data"]["lens_teasers"]
        assert "PERSONAL_LIFESTYLE" in teasers
        assert "STUDENT_SUCCESS" in teasers
        assert "PROFESSIONAL_LEADERSHIP" in teasers
        assert "FAMILY_ECOSYSTEM" in teasers
        for lens in teasers.values():
            assert "title" in lens
            assert "teaser" in lens
            assert len(lens["teaser"]) > 50  # at least 2-3 sentences

    def test_free_tier_has_locked_features(self, client):
        """Free ScoreCard should list 5 locked features."""
        payload = _make_response_payload(3)
        payload["tier"] = "free"
        resp = client.post("/api/v1/assess", json=payload)
        locked = resp.json()["data"]["locked_features"]
        assert len(locked) == 5
        for feat in locked:
            assert "name" in feat
            assert "message" in feat

    def test_default_tier_is_free(self, client):
        """Default tier should be free (ScoreCard)."""
        payload = _make_response_payload(3)
        resp = client.post("/api/v1/assess", json=payload)
        data = resp.json()["data"]
        assert data["tier"] == "free"


class TestResultRetrieval:
    """GET /api/v1/results/{id} and /api/v1/results/user/{user_id}"""

    def test_retrieve_stored_result(self, client):
        """Submit then retrieve by result_id."""
        payload = _make_response_payload(3)
        submit_resp = client.post("/api/v1/assess", json=payload)
        result_id = submit_resp.json()["result_id"]

        get_resp = client.get(f"/api/v1/results/{result_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["success"] is True

    def test_retrieve_nonexistent_result(self, client):
        """Unknown result_id should return 404."""
        resp = client.get("/api/v1/results/nonexistent_id")
        assert resp.status_code == 404

    def test_retrieve_user_results(self, client):
        """Submit then retrieve by user_id."""
        payload = _make_response_payload(3)
        client.post("/api/v1/assess", json=payload)

        resp = client.get("/api/v1/results/user/test_api_user")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) >= 1
