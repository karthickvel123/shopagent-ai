"""Unit tests for Razorpay client wrapper."""

from backend.razorpay_client import RazorpayClient


class TestRazorpayClient:
    def test_init_simulated_mode(self, rzp_client):
        assert rzp_client.key_id == "rzp_test_fixture"
        assert rzp_client.key_secret == "secret_fixture_123"

    def test_create_order_returns_dict(self, rzp_client):
        order = rzp_client.create_order(amount_paise=100000, currency="INR")
        assert "id" in order
        assert order["amount"] == 100000
        assert order["currency"] == "INR"
        assert order["status"] == "created"
        assert order["id"].startswith("order_")

    def test_create_order_with_receipt(self, rzp_client):
        order = rzp_client.create_order(amount_paise=50000, receipt="rcpt_test")
        assert order["receipt"] == "rcpt_test"

    def test_create_order_with_notes(self, rzp_client):
        order = rzp_client.create_order(
            amount_paise=75000,
            notes={"product": "test_product", "quantity": 1}
        )
        assert order["notes"]["product"] == "test_product"

    def test_fetch_order(self, rzp_client):
        order = rzp_client.fetch_order("order_abc123")
        assert order["id"] == "order_abc123"

    def test_simulate_test_payment(self, rzp_client):
        result = rzp_client.simulate_test_payment("order_abc123", method="upi")
        assert "payment_id" in result
        assert result["payment_id"].startswith("pay_")
        assert "signature" in result
        assert result["method"] == "upi"
        assert result["status"] == "captured"

    def test_simulate_payment_card_method(self, rzp_client):
        result = rzp_client.simulate_test_payment("order_xyz", method="card")
        assert result["method"] == "card"

    def test_verify_payment_signature_valid(self, rzp_client):
        order_id = "order_test_verify"
        sim = rzp_client.simulate_test_payment(order_id)
        is_valid = rzp_client.verify_payment_signature(
            razorpay_order_id=order_id,
            razorpay_payment_id=sim["payment_id"],
            razorpay_signature=sim["signature"]
        )
        assert is_valid is True

    def test_verify_payment_signature_invalid(self, rzp_client):
        is_valid = rzp_client.verify_payment_signature(
            razorpay_order_id="order_test",
            razorpay_payment_id="pay_wrong",
            razorpay_signature="tampered_signature_abc"
        )
        assert is_valid is False

    def test_verify_payment_signature_empty_fields(self, rzp_client):
        assert rzp_client.verify_payment_signature("", "", "") is False
        assert rzp_client.verify_payment_signature("order_1", "", "sig") is False


class TestRazorpayClientDefaultKeys:
    def test_no_keys_creates_mock(self):
        client = RazorpayClient(key_id="", key_secret="")
        assert client.is_live is False
        order = client.create_order(amount_paise=200000)
        assert "id" in order
