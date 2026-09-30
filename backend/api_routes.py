"""FastAPI router containing all REST endpoints for ShopAgent AI."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.schemas import (
    ChatRequest, ChatResponse, ProductOut, OrderOut,
    AuditLogOut, DashboardStats
)
from backend.database import get_db, engine, Base
from backend.agent import run_agent
from backend.catalog import seed_catalog, browse_catalog_db, get_product_by_id
from backend.models import Product, Order, Payment, AgentSession, AuditLog
from backend.optimizer import analyze_catalog_optimization, calculate_discoverability_score

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Receive shopper message, execute autonomous agent loop, and return response."""
    interaction_id = None
    if request.session_id:
        last_session = db.query(AgentSession).filter(
            AgentSession.session_id == request.session_id
        ).order_by(AgentSession.created_at.desc()).first()
        if last_session and last_session.interaction_id:
            interaction_id = last_session.interaction_id

    response = run_agent(
        user_message=request.message,
        db=db,
        session_id=request.session_id,
        previous_interaction_id=interaction_id
    )
    return response


@router.get("/api/products", response_model=List[ProductOut])
def get_products(
    category: Optional[str] = None,
    sort_by: Optional[str] = "popularity",
    limit: Optional[int] = 50,
    db: Session = Depends(get_db)
):
    """Retrieve catalog products with optional category and sorting."""
    raw_products = browse_catalog_db(db, category=category, sort_by=sort_by or "popularity", limit=limit or 50)
    # Map into ProductOut
    out = []
    for p in raw_products:
        out.append(ProductOut(
            id=p["id"],
            name=p["name"],
            description=p["description"],
            price=p["price_paise"],
            price_display=p["price_display"],
            category=p["category"],
            brand=p.get("brand", ""),
            stock=p.get("stock", 0),
            rating=p.get("rating", 0.0),
            review_count=p.get("review_count", 0),
            specs=p.get("specs", {}),
            ai_tags=p.get("ai_tags", []),
            ai_discoverability_score=p.get("ai_discoverability_score", 0.0)
        ))
    return out


@router.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Fetch details of a single product by ID."""
    p = get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return ProductOut(
        id=p["id"],
        name=p["name"],
        description=p["description"],
        price=p["price_paise"],
        price_display=p["price_display"],
        category=p["category"],
        brand=p.get("brand", ""),
        stock=p.get("stock", 0),
        rating=p.get("rating", 0.0),
        review_count=p.get("review_count", 0),
        specs=p.get("specs", {}),
        ai_tags=p.get("ai_tags", []),
        ai_discoverability_score=p.get("ai_discoverability_score", 0.0)
    )


@router.get("/api/orders", response_model=List[OrderOut])
def get_orders(db: Session = Depends(get_db)):
    """List recent orders."""
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(100).all()
    out = []
    for o in orders:
        out.append(OrderOut(
            id=o.id,
            razorpay_order_id=o.razorpay_order_id,
            product_id=o.product_id,
            quantity=o.quantity,
            amount=o.amount,
            amount_display=f"₹{o.amount / 100:,.0f}",
            currency=o.currency,
            status=o.status,
            customer_email=o.customer_email or "",
            created_at=o.created_at
        ))
    return out


@router.get("/api/orders/{razorpay_order_id}")
def get_order(razorpay_order_id: str, db: Session = Depends(get_db)):
    """Fetch order details including linked Razorpay payment verification."""
    order = db.query(Order).filter(
        (Order.razorpay_order_id == razorpay_order_id) | (Order.id == int(razorpay_order_id) if razorpay_order_id.isdigit() else False)
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "product_id": order.product_id,
        "product_name": order.product.name if order.product else "",
        "quantity": order.quantity,
        "amount_paise": order.amount,
        "amount_inr": order.amount / 100,
        "status": order.status,
        "customer_email": order.customer_email,
        "payment": {
            "payment_id": order.payment.razorpay_payment_id if order.payment else None,
            "method": order.payment.method if order.payment else None,
            "verified": order.payment.signature_verified if order.payment else False,
            "signature": order.payment.razorpay_signature if order.payment else None,
        } if order.payment else None,
        "created_at": order.created_at
    }


@router.get("/api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    """List agent conversation sessions."""
    sessions = db.query(AgentSession).order_by(AgentSession.created_at.desc()).limit(50).all()
    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "interaction_id": s.interaction_id,
            "user_query": s.user_query,
            "agent_response": s.agent_response,
            "tools_used": s.tools_used or [],
            "tool_call_count": s.tool_call_count or 0,
            "status": s.status,
            "created_at": s.created_at
        }
        for s in sessions
    ]


@router.get("/api/sessions/{session_id}/audit", response_model=List[AuditLogOut])
def get_session_audit(session_id: str, db: Session = Depends(get_db)):
    """Retrieve immutable audit trail for a specific agent session."""
    logs = db.query(AuditLog).filter(AuditLog.session_id == session_id).order_by(AuditLog.created_at.asc()).all()
    return [
        AuditLogOut(
            id=log.id,
            session_id=log.session_id,
            action=log.action,
            tool_name=log.tool_name or "",
            input_data=log.input_data or {},
            output_data=log.output_data or {},
            confidence=log.confidence or 0.0,
            latency_ms=log.latency_ms or 0.0,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.get("/api/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """Aggregated analytics for the real-time monitoring dashboard."""
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.amount)).filter(Order.status == 'paid').scalar() or 0
    total_sessions = db.query(func.count(AgentSession.id)).scalar() or 0
    total_tool_calls = db.query(func.sum(AgentSession.tool_call_count)).scalar() or 0
    avg_tools = float(total_tool_calls) / total_sessions if total_sessions > 0 else 0.0

    # Orders grouped by status
    status_counts = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    orders_by_status = {status: count for status, count in status_counts}

    # Top categories
    cat_counts = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    top_categories = [{"category": c[0], "count": c[1]} for c in cat_counts]

    # Recent orders
    recent_orders_db = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    recent_orders = [
        OrderOut(
            id=o.id,
            razorpay_order_id=o.razorpay_order_id,
            product_id=o.product_id,
            quantity=o.quantity,
            amount=o.amount,
            amount_display=f"₹{o.amount / 100:,.0f}",
            currency=o.currency,
            status=o.status,
            customer_email=o.customer_email or "",
            created_at=o.created_at
        )
        for o in recent_orders_db
    ]

    # Average discoverability score
    all_products = db.query(Product).filter(Product.is_active == True).all()
    opt_summary = analyze_catalog_optimization(all_products)

    return DashboardStats(
        total_products=total_products,
        total_orders=total_orders,
        total_revenue_paise=total_revenue,
        total_sessions=total_sessions,
        total_tool_calls=total_tool_calls,
        avg_tools_per_session=round(avg_tools, 2),
        orders_by_status=orders_by_status,
        top_categories=top_categories,
        recent_orders=recent_orders,
        avg_discoverability_score=opt_summary.get("average_score", 0.0)
    )


@router.get("/api/catalog/optimization")
def get_catalog_optimization(db: Session = Depends(get_db)):
    """Return store AI-discoverability audit metrics and actionable tips."""
    products = db.query(Product).filter(Product.is_active == True).all()
    return analyze_catalog_optimization(products)


@router.post("/api/seed-catalog")
def seed_catalog_endpoint(db: Session = Depends(get_db)):
    """Seed catalog with 20 demo products."""
    added = seed_catalog(db)
    return {"status": "ok", "message": f"Catalog seeded with {added} new products."}


@router.post("/api/reset")
def reset_database(db: Session = Depends(get_db)):
    """Reset database tables and seed fresh demo catalog."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    added = seed_catalog(db)
    return {"status": "ok", "message": f"Database reset successfully and seeded with {added} products."}
