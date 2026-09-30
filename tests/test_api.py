"""Integration tests for FastAPI endpoints."""


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ShopAgent" in data["service"]


class TestProductEndpoints:
    def test_list_products(self, client):
        response = client.get("/api/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) == 20

    def test_list_products_by_category(self, client):
        response = client.get("/api/products?category=electronics")
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        for p in products:
            assert p["category"] == "electronics"

    def test_get_product_by_id(self, client):
        response = client.get("/api/products/ELEC001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ELEC001"
        assert "Sony" in data["name"]

    def test_get_product_not_found(self, client):
        response = client.get("/api/products/NONEXIST")
        assert response.status_code == 404


class TestChatEndpoint:
    def test_chat_search(self, client):
        response = client.post("/api/chat", json={"message": "Find me wireless earbuds"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data
        assert len(data["response"]) > 0
        assert len(data["tools_used"]) >= 1

    def test_chat_purchase(self, client):
        response = client.post("/api/chat", json={"message": "Buy BOOK001"})
        assert response.status_code == 200
        data = response.json()
        assert data["tool_call_count"] >= 3

    def test_chat_empty_message(self, client):
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error


class TestOrderEndpoints:
    def test_list_orders_empty(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_order_after_purchase(self, client):
        # Place an order first
        client.post("/api/chat", json={"message": "Buy ELEC001"})
        response = client.get("/api/orders")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) >= 1
        assert orders[0]["status"] in ("created", "paid")


class TestSessionEndpoints:
    def test_list_sessions(self, client):
        client.post("/api/chat", json={"message": "hello"})
        response = client.get("/api/sessions")
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1

    def test_audit_trail(self, client):
        # Create a session with tool calls
        chat_resp = client.post("/api/chat", json={"message": "Search for gaming mouse"})
        session_id = chat_resp.json()["session_id"]
        response = client.get(f"/api/sessions/{session_id}/audit")
        assert response.status_code == 200


class TestStatsEndpoint:
    def test_stats(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert data["total_products"] == 20
        assert "total_orders" in data
        assert "total_sessions" in data


class TestCatalogOptimization:
    def test_optimization_endpoint(self, client):
        response = client.get("/api/catalog/optimization")
        assert response.status_code == 200
        data = response.json()
        assert "average_score" in data
        assert data["total_products"] == 20


class TestSeedAndReset:
    def test_seed_catalog(self, client):
        response = client.post("/api/seed-catalog")
        assert response.status_code == 200

    def test_reset(self, client):
        response = client.post("/api/reset")
        assert response.status_code == 200
