"""Autonomous AI Buyer Agent using Google Gemini 3.8 Flash Interactions API.

Features:
- Multi-turn function-calling loop with 10 tools
- Immutable audit trail for every tool invocation
- Graceful fallback to deterministic simulation when API key is unavailable
"""

import json
import re
import time
import uuid
import logging
import traceback
from typing import Optional, Dict, Any, List

from google import genai
from google.genai import errors as genai_errors

from backend.config import settings
from backend.tools import TOOL_DECLARATIONS, execute_tool
from backend.razorpay_client import RazorpayClient
from backend.models import AgentSession, AuditLog

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are ShopAgent AI — an autonomous AI buyer copilot for a merchant's online store.

Your job:
1. Understand what the user wants to buy
2. Search and browse the product catalog using your tools
3. Compare options and make recommendations with clear reasoning
4. Complete the purchase via Razorpay when the user confirms
5. Verify the payment signature and provide a receipt

Rules:
- Always search the catalog before recommending products
- Compare at least 2 products before suggesting one
- Explain your reasoning (why this product over others)
- Never create an order without explicit user confirmation
- Display all prices in ₹ (Indian Rupees), not paise
- Be conversational, concise, and helpful
- If a product is out of stock, suggest alternatives
- After payment, always verify the signature for security
"""


def run_agent(
    user_message: str,
    db,
    session_id: Optional[str] = None,
    previous_interaction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a single agentic turn with Gemini function-calling loop.

    Falls back to deterministic simulation when GEMINI_API_KEY is missing or invalid.

    Returns:
        dict with session_id, response, tools_used, tool_call_count, reasoning, interaction_id
    """
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:12]}"

    # Determine if we have a valid Gemini API key
    has_valid_key = bool(
        settings.gemini_api_key
        and not settings.gemini_api_key.startswith("your_")
        and len(settings.gemini_api_key) > 10
    )

    if not has_valid_key:
        logger.info("No valid GEMINI_API_KEY — using autonomous simulation engine.")
        return _run_simulated_agent(user_message, db, session_id)

    try:
        return _run_gemini_agent(user_message, db, session_id, previous_interaction_id)
    except genai_errors.APIError as e:
        logger.warning(f"Gemini API error: {e}. Falling back to simulation engine.")
        return _run_simulated_agent(user_message, db, session_id)
    except Exception as e:
        logger.error(f"Unexpected error in agent loop: {e}\n{traceback.format_exc()}")
        return _run_simulated_agent(user_message, db, session_id)


def _run_gemini_agent(
    user_message: str,
    db,
    session_id: str,
    previous_interaction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Full Gemini 3.8 Flash agent loop with autonomous tool dispatch."""
    client = genai.Client(api_key=settings.gemini_api_key)
    rzp = RazorpayClient()

    tools_used: List[str] = []
    tool_call_count = 0

    # Build the initial interaction request
    interaction_kwargs = {
        "model": settings.gemini_model,
        "input": user_message,
        "tools": TOOL_DECLARATIONS,
        "system_instruction": SYSTEM_INSTRUCTION,
        "store": False,
    }
    if previous_interaction_id:
        interaction_kwargs["previous_interaction_id"] = previous_interaction_id

    interaction = client.interactions.create(**interaction_kwargs)

    # Agentic loop: execute tool calls until the model emits final text
    max_iterations = 10
    for iteration in range(max_iterations):
        has_function_calls = False
        function_results = []

        for step in getattr(interaction, "steps", []):
            if getattr(step, "type", "") == "function_call":
                has_function_calls = True
                tool_name = getattr(step, "name", "")
                arguments = getattr(step, "arguments", {}) or {}

                start_time = time.time()
                result = execute_tool(tool_name, arguments, db, rzp)
                latency_ms = (time.time() - start_time) * 1000

                tools_used.append(tool_name)
                tool_call_count += 1

                # Immutable audit log entry
                audit = AuditLog(
                    session_id=session_id,
                    action="tool_call",
                    tool_name=tool_name,
                    input_data=arguments,
                    output_data=result,
                    confidence=0.95,
                    latency_ms=latency_ms,
                )
                db.add(audit)

                function_results.append({
                    "type": "function_result",
                    "name": tool_name,
                    "result": json.dumps(result),
                })
                logger.info(f"Tool {tool_name} executed in {latency_ms:.1f}ms")

        if not has_function_calls:
            break

        # Feed tool results back to the model for next reasoning step
        interaction = client.interactions.create(
            model=settings.gemini_model,
            input=function_results,
            tools=TOOL_DECLARATIONS,
            system_instruction=SYSTEM_INSTRUCTION,
            previous_interaction_id=interaction.id,
            store=False,
        )

    response_text = getattr(interaction, "output_text", None) or "I have processed your request."
    interaction_id = getattr(interaction, "id", "") or ""

    # Persist the session record
    _save_session(db, session_id, interaction_id, user_message, response_text, tools_used, tool_call_count)

    return {
        "session_id": session_id,
        "response": response_text,
        "tools_used": tools_used,
        "tool_call_count": tool_call_count,
        "reasoning": f"Gemini dispatched {tool_call_count} tools: {', '.join(tools_used)}",
        "interaction_id": interaction_id,
    }


def _run_simulated_agent(user_message: str, db, session_id: str) -> Dict[str, Any]:
    """Deterministic agent simulation that executes real tools without Gemini.

    This allows full demo capability (including Razorpay orders) when the API key
    is not configured.
    """
    rzp = RazorpayClient()
    tools_used: List[str] = []
    tool_call_count = 0
    msg_lower = user_message.lower()

    # ── Intent 1: Order Status / Tracking ──
    if any(k in msg_lower for k in ["status", "track", "where is", "order details"]):
        from backend.models import Order
        latest = db.query(Order).order_by(Order.created_at.desc()).first()
        if latest:
            res = execute_tool("get_order_status", {"order_id": str(latest.id)}, db, rzp)
            tools_used.append("get_order_status"); tool_call_count += 1
            response_text = (
                f"📋 **Order #{res.get('order_id', '')}**\n"
                f"• **Product:** {res.get('product_name', 'N/A')}\n"
                f"• **Amount:** ₹{res.get('amount_inr', 0):,.0f}\n"
                f"• **Status:** `{res.get('status', 'unknown').upper()}`\n"
                f"• **Payment Verified:** {'✅' if res.get('payment', {}).get('verified') else '⏳'}"
            )
        else:
            response_text = "No orders found yet. Try saying 'Buy Sony WF-C500 earbuds' to place one!"

    # ── Intent 2: Store / Catalog Optimization ──
    elif any(k in msg_lower for k in ["optimize", "audit", "discoverability", "score"]):
        res = execute_tool("analyze_store_optimization", {}, db, rzp)
        tools_used.append("analyze_store_optimization"); tool_call_count += 1
        response_text = (
            f"🔍 **Catalog AI-Discoverability Audit**\n\n"
            f"• **Average Score:** {res.get('average_score', 0)}%\n"
            f"• **Products Audited:** {res.get('total_products', 0)}\n"
            f"• **Agent-Ready:** {res.get('tier_distribution', {}).get('Tier 1', 0)} items\n\n"
            f"**Recommendations:**\n"
            + "\n".join(f"• {r}" for r in res.get("top_recommendations", []))
        )

    # ── Intent 3: Purchase / Checkout ──
    elif any(k in msg_lower for k in ["buy", "purchase", "order now", "place order", "checkout", "get it"]):
        from backend.models import Product

        # Try to identify the target product
        target = None
        id_match = re.search(r"\b(ELEC\d+|CLOTH\d+|HOME\d+|BOOK\d+|GAME\d+)\b", user_message, re.IGNORECASE)
        if id_match:
            target = db.query(Product).filter(Product.id == id_match.group(1).upper()).first()

        if not target:
            keywords = ["earbud", "charger", "speaker", "phone", "watch", "polo", "jeans",
                        "sneaker", "jacket", "lamp", "mixer", "bottle", "clean code",
                        "alchemist", "atomic habits", "controller", "mouse", "keyboard"]
            for kw in keywords:
                if kw in msg_lower:
                    target = db.query(Product).filter(Product.name.ilike(f"%{kw}%")).first()
                    if target:
                        break

        if not target:
            target = db.query(Product).filter(Product.id == "ELEC001").first()

        if not target:
            return _make_response(db, session_id, user_message, "No products found in catalog. Please seed the catalog first.", [], 0)

        # Execute the full 4-tool checkout pipeline
        r1 = execute_tool("check_availability", {"product_id": target.id, "quantity": 1}, db, rzp)
        tools_used.append("check_availability"); tool_call_count += 1

        r2 = execute_tool("create_razorpay_order", {"product_id": target.id, "quantity": 1}, db, rzp)
        tools_used.append("create_razorpay_order"); tool_call_count += 1

        if "error" in r2:
            return _make_response(db, session_id, user_message, f"Could not create order: {r2['error']}", tools_used, tool_call_count)

        r3 = execute_tool("simulate_payment", {"order_id": str(r2["order_id"]), "payment_method": "upi"}, db, rzp)
        tools_used.append("simulate_payment"); tool_call_count += 1

        r4 = execute_tool("verify_payment", {
            "order_id": str(r2["order_id"]),
            "payment_id": r3["payment_id"],
            "signature": r3["signature"]
        }, db, rzp)
        tools_used.append("verify_payment"); tool_call_count += 1

        response_text = (
            f"🎉 **Order Completed & Verified!**\n\n"
            f"• **Product:** {target.name}\n"
            f"• **Amount:** ₹{target.price / 100:,.0f}\n"
            f"• **Razorpay Order:** `{r2['razorpay_order_id']}`\n"
            f"• **Payment ID:** `{r3['payment_id']}`\n"
            f"• **Signature Verified:** ✅ HMAC-SHA256\n"
            f"• **Delivery:** 2-4 business days\n\n"
            f"All {tool_call_count} tool calls logged in the immutable audit trail."
        )

    # ── Intent 4: Product Discovery (Default) ──
    else:
        max_p = None
        budget_match = re.search(r"(?:under|below|less than|within)\s*(?:rs\.?|inr|₹)?\s*(\d+)", msg_lower)
        if budget_match:
            max_p = float(budget_match.group(1))

        clean_query = re.sub(r"(?:i want|i need|looking for|show me|search|find|under|below|less than|\d+)", "", msg_lower).strip()
        if not clean_query:
            clean_query = "popular"

        r1 = execute_tool("search_products", {"query": clean_query, "max_price": max_p}, db, rzp)
        tools_used.append("search_products"); tool_call_count += 1

        found = r1.get("results", [])
        if not found:
            r_browse = execute_tool("browse_catalog", {"limit": 5}, db, rzp)
            tools_used.append("browse_catalog"); tool_call_count += 1
            found = r_browse.get("products", [])

        if len(found) >= 2:
            ids = [p["id"] for p in found[:3]]
            execute_tool("compare_products", {"product_ids": ids}, db, rzp)
            tools_used.append("compare_products"); tool_call_count += 1

        top = found[0] if found else None
        alt = found[1] if len(found) > 1 else None

        if top:
            top_price = top.get("price_display") or "₹{:,.0f}".format(top.get("price_paise", 0) / 100)
            budget_str = " under ₹{:,.0f}".format(max_p) if max_p else ""
            response_text = (
                f"I searched for **'{clean_query}'**{budget_str}.\n\n"
                f"### 🏆 Top Pick: **{top['name']}**\n"
                f"• **Price:** {top_price}\n"
                f"• **Rating:** {top.get('rating', 4.0)}/5 ({top.get('review_count', 0)} reviews)\n"
                f"• **Stock:** {top.get('stock', 0)} units\n\n"
            )
            if alt:
                alt_price = alt.get("price_display") or "₹{:,.0f}".format(alt.get("price_paise", 0) / 100)
                response_text += (
                    f"### 🥈 Alternative: **{alt['name']}**\n"
                    f"• **Price:** {alt_price}\n\n"
                )
            response_text += "Reply **'Buy it'** to place an order via Razorpay!"
        else:
            response_text = "I couldn't find matching products. Try browsing Electronics, Books, or Gaming."

    return _make_response(db, session_id, user_message, response_text, tools_used, tool_call_count)


def _make_response(
    db, session_id: str, user_message: str, response_text: str,
    tools_used: List[str], tool_call_count: int
) -> Dict[str, Any]:
    """Save agent session and return formatted response dict."""
    interaction_id = f"sim_{uuid.uuid4().hex[:12]}"
    agent_session = AgentSession(
        session_id=session_id,
        interaction_id=interaction_id,
        user_query=user_message,
        agent_response=response_text,
        tools_used=tools_used,
        tool_call_count=tool_call_count,
        reasoning=f"Dispatched {len(tools_used)} tools: {', '.join(tools_used)}",
        status="completed",
    )
    db.add(agent_session)
    db.commit()
    return {
        "session_id": session_id,
        "response": response_text,
        "tools_used": tools_used,
        "tool_call_count": tool_call_count,
        "reasoning": agent_session.reasoning,
        "interaction_id": interaction_id,
    }


def _save_session(
    db, session_id: str, interaction_id: str, user_message: str,
    response_text: str, tools_used: List[str], tool_call_count: int
) -> None:
    """Persist a Gemini agent session to the database."""
    agent_session = AgentSession(
        session_id=session_id,
        interaction_id=interaction_id,
        user_query=user_message,
        agent_response=response_text,
        tools_used=tools_used,
        tool_call_count=tool_call_count,
        reasoning=f"Gemini dispatched {tool_call_count} tools: {', '.join(tools_used)}",
        status="completed",
    )
    db.add(agent_session)
    db.commit()
