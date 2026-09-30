"""Unit tests for the agent simulation engine (no Gemini API key required)."""

from backend.agent import run_agent, _run_simulated_agent


class TestAgentSimulation:
    """Tests the deterministic simulation fallback agent."""

    def test_product_search_flow(self, db_session):
        result = _run_simulated_agent("I need wireless earbuds under 4000", db_session, "test_sess_1")
        assert result["session_id"] == "test_sess_1"
        assert "search_products" in result["tools_used"]
        assert result["tool_call_count"] >= 1
        assert len(result["response"]) > 0

    def test_purchase_flow(self, db_session):
        result = _run_simulated_agent("Buy Sony WF-C500 earbuds", db_session, "test_sess_2")
        assert "check_availability" in result["tools_used"]
        assert "create_razorpay_order" in result["tools_used"]
        assert "simulate_payment" in result["tools_used"]
        assert "verify_payment" in result["tools_used"]
        assert result["tool_call_count"] == 4
        assert "Verified" in result["response"] or "verified" in result["response"].lower()

    def test_purchase_by_id(self, db_session):
        result = _run_simulated_agent("Buy ELEC004", db_session, "test_sess_3")
        assert result["tool_call_count"] == 4
        assert "JBL" in result["response"]

    def test_order_status_no_orders(self, db_session):
        result = _run_simulated_agent("What's my order status?", db_session, "test_sess_status_none")
        # Should handle gracefully when no orders exist
        assert len(result["response"]) > 0

    def test_order_status_with_order(self, db_session):
        # First create an order
        _run_simulated_agent("Buy BOOK001", db_session, "test_sess_buy_first")
        # Then check status with a different session id
        result = _run_simulated_agent("Track my order", db_session, "test_sess_track_it")
        assert "get_order_status" in result["tools_used"]

    def test_store_optimization(self, db_session):
        result = _run_simulated_agent("Audit my store discoverability", db_session, "test_sess_6")
        assert "analyze_store_optimization" in result["tools_used"]
        assert "%" in result["response"]

    def test_generic_browsing(self, db_session):
        result = _run_simulated_agent("Show me some gaming accessories", db_session, "test_sess_7")
        assert "search_products" in result["tools_used"]
        assert result["tool_call_count"] >= 1

    def test_fallback_browse(self, db_session):
        result = _run_simulated_agent("hello", db_session, "test_sess_8")
        assert result["tool_call_count"] >= 1


class TestRunAgentFallback:
    """Tests run_agent() falls back to simulation when no API key is set."""

    def test_no_api_key_uses_simulation(self, db_session):
        result = run_agent("Find me a good smartphone", db_session, session_id="test_run_1")
        assert result["session_id"] == "test_run_1"
        assert len(result["tools_used"]) >= 1
        assert len(result["response"]) > 10

    def test_session_id_auto_generated(self, db_session):
        result = run_agent("Browse electronics", db_session)
        assert result["session_id"].startswith("session_")
