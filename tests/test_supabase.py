"""
Tests for Supabase integration.
Tests the client initialization, database operations, and API with Supabase.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestSupabaseClient:
    """Test Supabase client module."""

    def test_missing_credentials_raises_error(self):
        """Should raise RuntimeError if SUPABASE_URL is empty."""
        from scoring_engine.supabase_client import reset_client
        reset_client()

        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""}, clear=False):
            with patch("scoring_engine.supabase_client.SUPABASE_URL", ""):
                with patch("scoring_engine.supabase_client.SUPABASE_ANON_KEY", ""):
                    from scoring_engine.supabase_client import get_supabase_client
                    with pytest.raises(RuntimeError, match="Supabase credentials not configured"):
                        get_supabase_client()

        reset_client()

    def test_reset_client(self):
        """reset_client should clear the singleton."""
        from scoring_engine.supabase_client import reset_client, _client
        reset_client()
        from scoring_engine import supabase_client
        assert supabase_client._client is None


class TestDatabaseModule:
    """Test database.py functions with mocked Supabase client."""

    def _make_full_output(self):
        """Create a minimal full_output dict for testing."""
        return {
            "metadata": {
                "assessment_id": "TEST",
                "user_id": "test_user",
                "completion_rate": 1.0,
                "low_confidence": False,
                "demographics": None,
            },
            "construct_scores": {"PEI_score": 0.5, "BHP_score": 0.6},
            "load_framework": {
                "quadrant": "Q1_Aligned_Flow",
                "load_state": "Stable_Capacity",
                "load_balance": 0.1,
            },
            "archetype": {"archetype_id": "THE_OPTIMIZER"},
            "domains": [],
        }

    def test_store_result_calls_insert(self):
        """store_result should call Supabase insert."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "test-id"}])

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import store_result
            result_id = store_result(
                user_id="test_user",
                report_type="STUDENT_SUCCESS",
                raw_responses=[{"item_id": "Q01", "response": 3}],
                full_output=self._make_full_output(),
            )

        assert result_id is not None
        mock_client.table.assert_called_with("assessment_results")
        mock_table.insert.assert_called_once()

    def test_get_result_by_id_found(self):
        """get_result_by_id should return full_output when found."""
        full_output = self._make_full_output()
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data={"full_output": full_output})

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import get_result_by_id
            result = get_result_by_id("test-id")

        assert result == full_output

    def test_get_result_by_id_not_found(self):
        """get_result_by_id should return None when not found."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=None)

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import get_result_by_id
            result = get_result_by_id("nonexistent")

        assert result is None

    def test_get_results_by_user(self):
        """get_results_by_user should return list of results."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[
            {"id": "r1", "report_type": "STUDENT_SUCCESS", "quadrant": "Q1_Aligned_Flow",
             "archetype_id": "THE_OPTIMIZER", "pei_score": 0.4, "bhp_score": 0.6,
             "created_at": "2026-03-24T00:00:00Z"},
        ])

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import get_results_by_user
            results = get_results_by_user("test_user")

        assert len(results) == 1
        assert results[0]["id"] == "r1"

    def test_get_results_by_user_empty(self):
        """get_results_by_user should return empty list for unknown user."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import get_results_by_user
            results = get_results_by_user("unknown_user")

        assert results == []

    def test_check_connection_success(self):
        """check_connection should return True when Supabase is reachable."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])

        with patch("scoring_engine.database._get_client", return_value=mock_client):
            from scoring_engine.database import check_connection
            assert check_connection() is True

    def test_check_connection_failure(self):
        """check_connection should return False when Supabase is unreachable."""
        with patch("scoring_engine.database._get_client", side_effect=Exception("Connection failed")):
            from scoring_engine.database import check_connection
            assert check_connection() is False


class TestAPIWithSupabase:
    """Test API endpoints work in both in-memory and Supabase modes."""

    def test_health_shows_in_memory_mode(self):
        """Health check should show in-memory mode when no DB."""
        from scoring_engine.api import create_app
        from fastapi.testclient import TestClient

        app = create_app(use_database=False)
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "in-memory" in resp.json()["database"]

    def test_assess_works_without_supabase(self):
        """Assessment should work in in-memory fallback mode."""
        from scoring_engine.api import create_app
        from scoring_engine.item_dictionary import ITEM_DICTIONARY
        from fastapi.testclient import TestClient

        app = create_app(use_database=False)
        client = TestClient(app)

        payload = {
            "user_id": "test_user",
            "report_type": "STUDENT_SUCCESS",
            "responses": [
                {"item_id": item["item_id"], "response": 3}
                for item in ITEM_DICTIONARY
            ],
        }
        resp = client.post("/api/v1/assess", json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
