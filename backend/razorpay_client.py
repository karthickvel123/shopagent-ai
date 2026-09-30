"""Razorpay client wrapper for order creation, signature verification, and simulation."""

import hmac
import hashlib
import time
import uuid
import logging
from typing import Dict, Any, Optional

try:
    import razorpay
except ImportError:
    razorpay = None

from backend.config import settings

logger = logging.getLogger(__name__)


class RazorpayClient:
    """Wrapper around official Razorpay SDK with test simulation capabilities."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or settings.razorpay_key_id
        self.key_secret = key_secret or settings.razorpay_key_secret
        self.is_live = bool(self.key_id and self.key_secret and razorpay is not None)

        if self.is_live:
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
                logger.info("Razorpay client initialized with provided credentials.")
            except Exception as e:
                logger.warning(f"Failed to initialize Razorpay SDK client: {e}. Falling back to mock mode.")
                self.client = None
                self.is_live = False
        else:
            self.client = None
            logger.info("Razorpay client operating in simulated test mode.")

    def create_order(
        self,
        amount_paise: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay order via API or simulation."""
        receipt_id = receipt or f"rcpt_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        data = {
            "amount": int(amount_paise),
            "currency": currency,
            "receipt": receipt_id,
            "notes": notes or {"created_by": "ShopAgent_AI"},
        }

        if self.is_live and self.client:
            try:
                order = self.client.order.create(data=data)
                return order
            except Exception as e:
                logger.error(f"Live Razorpay order creation failed: {e}. Falling back to simulation.")

        # Simulated Razorpay order
        simulated_order_id = f"order_{uuid.uuid4().hex[:14]}"
        return {
            "id": simulated_order_id,
            "entity": "order",
            "amount": int(amount_paise),
            "amount_paid": 0,
            "amount_due": int(amount_paise),
            "currency": currency,
            "receipt": receipt_id,
            "status": "created",
            "attempts": 0,
            "notes": data["notes"],
            "created_at": int(time.time()),
        }

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch details of an existing Razorpay order."""
        if self.is_live and self.client:
            try:
                return self.client.order.fetch(order_id)
            except Exception as e:
                logger.error(f"Error fetching order {order_id} from Razorpay: {e}")

        return {
            "id": order_id,
            "entity": "order",
            "status": "created",
            "currency": "INR",
        }

    def simulate_test_payment(
        self,
        order_id: str,
        method: str = "card",
    ) -> Dict[str, Any]:
        """Generate a valid test payment ID and signature for an order."""
        payment_id = f"pay_{uuid.uuid4().hex[:14]}"
        msg = f"{order_id}|{payment_id}"
        secret = self.key_secret or "test_secret_for_shopagent"
        signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "signature": signature,
            "method": method,
            "status": "captured",
        }

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify HMAC-SHA256 signature for Razorpay checkout."""
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return False

        secret = self.key_secret or "test_secret_for_shopagent"
        expected = hmac.new(
            secret.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, razorpay_signature)
