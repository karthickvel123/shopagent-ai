"""Unit tests for the 10 function-calling tools."""

from backend.tools import TOOL_DECLARATIONS, execute_tool
from backend.models import Product, Order, Payment


class TestToolDeclarations:
    def test_has_10_tools(self):
        assert len(TOOL_DECLARATIONS) == 10

    def test_all_tools_have_required_fields(self):
        for tool in TOOL_DECLARATIONS:
            assert tool["type"] == "function"
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert tool["parameters"]["type"] == "object"

    def test_tool_names_unique(self):
        names = [t["name"] for t in TOOL_DECLARATIONS]
        assert len(names) == len(set(names))

    def test_expected_tool_names(self):
        names = {t["name"] for t in TOOL_DECLARATIONS}
        expected = {
            "browse_catalog", "search_products", "get_product_details",
            "compare_products", "check_availability", "create_razorpay_order",
            "simulate_payment", "verify_payment", "get_order_status",
            "analyze_store_optimization"
        }
        assert names == expected


class TestBrowseCatalogTool:
    def test_returns_products(self, db_session, rzp_client):
        result = execute_tool("browse_catalog", {}, db_session, rzp_client)
        assert "products" in result
        assert result["count"] > 0

    def test_with_category(self, db_session, rzp_client):
        result = execute_tool("browse_catalog", {"category": "books"}, db_session, rzp_client)
        assert result["count"] > 0


class TestSearchProductsTool:
    def test_search(self, db_session, rzp_client):
        result = execute_tool("search_products", {"query": "earbuds"}, db_session, rzp_client)
        assert "results" in result
        assert result["count"] > 0

    def test_search_with_price_filter(self, db_session, rzp_client):
        result = execute_tool("search_products", {"query": "speaker", "max_price": 5000}, db_session, rzp_client)
        assert isinstance(result["results"], list)


class TestGetProductDetailsTool:
    def test_found(self, db_session, rzp_client):
        result = execute_tool("get_product_details", {"product_id": "ELEC001"}, db_session, rzp_client)
        assert result["id"] == "ELEC001"
        assert "price_display" in result

    def test_not_found(self, db_session, rzp_client):
        result = execute_tool("get_product_details", {"product_id": "XXX"}, db_session, rzp_client)
        assert "error" in result


class TestCompareProductsTool:
    def test_compare(self, db_session, rzp_client):
        result = execute_tool("compare_products", {"product_ids": ["ELEC001", "ELEC004"]}, db_session, rzp_client)
        assert result["compared_count"] == 2


class TestCheckAvailabilityTool:
    def test_available(self, db_session, rzp_client):
        result = execute_tool("check_availability", {"product_id": "ELEC001"}, db_session, rzp_client)
        assert result["available"] is True

    def test_not_available(self, db_session, rzp_client):
        result = execute_tool("check_availability", {"product_id": "ELEC001", "quantity": 99999}, db_session, rzp_client)
        assert result["available"] is False


class TestOrderPipelineTools:
    def test_full_checkout_pipeline(self, db_session, rzp_client):
        """Test the complete 4-tool checkout: create → pay → verify → status."""
        # 1. Create order
        r1 = execute_tool("create_razorpay_order", {"product_id": "BOOK001", "quantity": 1}, db_session, rzp_client)
        assert "razorpay_order_id" in r1
        assert "order_id" in r1
        order_id = str(r1["order_id"])

        # 2. Simulate payment
        r2 = execute_tool("simulate_payment", {"order_id": order_id, "payment_method": "upi"}, db_session, rzp_client)
        assert r2["status"] == "success"
        assert "payment_id" in r2

        # 3. Verify signature
        r3 = execute_tool("verify_payment", {
            "order_id": order_id,
            "payment_id": r2["payment_id"],
            "signature": r2["signature"]
        }, db_session, rzp_client)
        assert r3["verified"] is True

        # 4. Get status
        r4 = execute_tool("get_order_status", {"order_id": order_id}, db_session, rzp_client)
        assert r4["status"] == "paid"

    def test_create_order_insufficient_stock(self, db_session, rzp_client):
        result = execute_tool("create_razorpay_order", {"product_id": "ELEC001", "quantity": 99999}, db_session, rzp_client)
        assert "error" in result
        assert "Insufficient" in result["error"]

    def test_create_order_product_not_found(self, db_session, rzp_client):
        result = execute_tool("create_razorpay_order", {"product_id": "NONEXIST"}, db_session, rzp_client)
        assert "error" in result


class TestOptimizationTool:
    def test_single_product(self, db_session, rzp_client):
        result = execute_tool("analyze_store_optimization", {"product_id": "ELEC001"}, db_session, rzp_client)
        assert "discoverability_score" in result
        assert result["discoverability_score"] > 0

    def test_full_catalog(self, db_session, rzp_client):
        result = execute_tool("analyze_store_optimization", {}, db_session, rzp_client)
        assert "average_score" in result
        assert result["total_products"] == 20

    def test_product_not_found(self, db_session, rzp_client):
        result = execute_tool("analyze_store_optimization", {"product_id": "XXX"}, db_session, rzp_client)
        assert "error" in result


class TestUnknownTool:
    def test_unknown_tool(self, db_session, rzp_client):
        result = execute_tool("nonexistent_tool", {}, db_session, rzp_client)
        assert "error" in result

    def test_latency_tracked(self, db_session, rzp_client):
        result = execute_tool("browse_catalog", {}, db_session, rzp_client)
        assert "_latency_ms" in result
        assert result["_latency_ms"] >= 0
