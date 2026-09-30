"""SQLAlchemy ORM models for ShopAgent AI."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, JSON,
    DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Product(Base):
    """Merchant product catalog entry."""

    __tablename__ = "products"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False, doc="Price in paise (INR × 100)")
    category = Column(String(100), nullable=False, index=True)
    brand = Column(String(100), default="")
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    image_url = Column(String(500), default="")
    specs = Column(JSON, default=dict, doc="Product specifications as key-value pairs")
    ai_tags = Column(JSON, default=list, doc="Tags for AI-discoverability")
    ai_discoverability_score = Column(Float, default=0.0, doc="0.0–1.0 score for how AI-findable this product is")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="product")


class Order(Base):
    """Purchase order linked to Razorpay."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    razorpay_order_id = Column(String(100), unique=True, index=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    amount = Column(Integer, nullable=False, doc="Total in paise")
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="created", doc="created | paid | failed | refunded")
    customer_email = Column(String(255), default="")
    customer_phone = Column(String(20), default="")
    agent_session_id = Column(String(100), default="", doc="Links to the agent session that created this order")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False)


class Payment(Base):
    """Payment record with Razorpay signature verification."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    razorpay_payment_id = Column(String(100), default="")
    razorpay_order_id = Column(String(100), default="")
    razorpay_signature = Column(String(255), default="")
    amount = Column(Integer, nullable=False, doc="Amount in paise")
    method = Column(String(30), default="", doc="card | upi | netbanking | wallet")
    status = Column(String(30), default="pending", doc="pending | captured | failed")
    signature_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="payment")


class AgentSession(Base):
    """Tracks a conversation session between user and agent."""

    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, index=True)
    interaction_id = Column(String(200), default="", doc="Gemini Interaction ID for multi-turn context")
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, default="")
    tools_used = Column(JSON, default=list, doc="List of tool names invoked in this turn")
    tool_call_count = Column(Integer, default=0)
    reasoning = Column(Text, default="", doc="Agent's internal reasoning chain")
    status = Column(String(30), default="active", doc="active | completed | error")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    audit_logs = relationship("AuditLog", back_populates="session")


class AuditLog(Base):
    """Immutable audit trail for every agent action."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey("agent_sessions.session_id"), nullable=False)
    action = Column(String(100), nullable=False, doc="Action type: tool_call | decision | error | payment")
    tool_name = Column(String(100), default="")
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    confidence = Column(Float, default=0.0, doc="Agent confidence in this action 0.0–1.0")
    latency_ms = Column(Float, default=0.0, doc="Execution time in milliseconds")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("AgentSession", back_populates="audit_logs")


class StoreOptimization(Base):
    """AI-discoverability optimization suggestions for products."""

    __tablename__ = "store_optimizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False)
    current_score = Column(Float, default=0.0)
    suggested_score = Column(Float, default=0.0)
    suggestions = Column(JSON, default=list, doc="List of improvement suggestions")
    category = Column(String(50), default="", doc="general | seo | description | pricing | tags")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
