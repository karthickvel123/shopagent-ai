"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Chat / Agent ──────────────────────────────────────────

class ChatRequest(BaseModel):
    """User message sent to the AI agent."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Existing session ID for multi-turn chat")


class ChatResponse(BaseModel):
    """Agent response with metadata."""
    session_id: str
    response: str
    tools_used: list[str] = []
    tool_call_count: int = 0
    reasoning: str = ""


# ── Products ──────────────────────────────────────────────

class ProductOut(BaseModel):
    """Product data returned to the client."""
    id: str
    name: str
    description: str
    price: int
    price_display: str = ""
    category: str
    brand: str = ""
    stock: int = 0
    rating: float = 0.0
    review_count: int = 0
    image_url: str = ""
    specs: dict = {}
    ai_tags: list[str] = []
    ai_discoverability_score: float = 0.0

    class Config:
        from_attributes = True


# ── Orders ────────────────────────────────────────────────

class OrderOut(BaseModel):
    """Order data returned to the client."""
    id: int
    razorpay_order_id: str
    product_id: str
    quantity: int
    amount: int
    amount_display: str = ""
    currency: str
    status: str
    customer_email: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Payments ──────────────────────────────────────────────

class PaymentOut(BaseModel):
    """Payment data returned to the client."""
    id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: int
    method: str
    status: str
    signature_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Audit ─────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    """Audit log entry returned to the client."""
    id: int
    session_id: str
    action: str
    tool_name: str = ""
    input_data: dict = {}
    output_data: dict = {}
    confidence: float = 0.0
    latency_ms: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Dashboard Stats ───────────────────────────────────────

class DashboardStats(BaseModel):
    """Aggregated statistics for the monitoring dashboard."""
    total_products: int = 0
    total_orders: int = 0
    total_revenue_paise: int = 0
    total_sessions: int = 0
    total_tool_calls: int = 0
    avg_tools_per_session: float = 0.0
    orders_by_status: dict = {}
    top_categories: list[dict] = []
    recent_orders: list[OrderOut] = []
    avg_discoverability_score: float = 0.0
