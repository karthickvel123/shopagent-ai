"""Function-calling tool definitions and router for Gemini 3.8 Flash."""

import time
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.models import Product, Order, Payment
from backend import catalog
from backend.razorpay_client import RazorpayClient
from backend.optimizer import calculate_discoverability_score

logger = logging.getLogger(__name__)

TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "browse_catalog",
        "description": "Browse the merchant product catalog with optional filtering by category and sorting.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category to filter by (e.g. electronics, clothing, home, books, gaming)."},
                "sort_by": {"type": "string", "enum": ["price_asc", "price_desc", "popularity", "newest", "rating"], "description": "Sorting criteria."},
                "limit": {"type": "integer", "description": "Maximum number of results to return (default 10)."}
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "search_products",
        "description": "Search for products based on natural language query with optional budget filters in Rupees (INR).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text (e.g. 'wireless earbuds with bass', 'jeans', 'charger')."},
                "min_price": {"type": "number", "description": "Minimum price in INR (Rupees)."},
                "max_price": {"type": "number", "description": "Maximum price in INR (Rupees)."}
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "get_product_details",
        "description": "Get complete detailed technical specifications, reviews, price, and stock for a specific product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID (e.g. 'ELEC001')."}
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "compare_products",
        "description": "Compare 2 or more products side-by-side on price, specs, rating, and value proposition.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to compare (e.g. ['ELEC001', 'ELEC004'])."
                }
            },
            "required": ["product_ids"]
        }
    },
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check if a product is in stock and available for immediate shipping for a desired quantity.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID."},
                "quantity": {"type": "integer", "description": "Quantity requested (defaults to 1)."}
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "create_razorpay_order",
        "description": "Create an official Razorpay order for purchasing an item after receiving buyer confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID to purchase."},
                "quantity": {"type": "integer", "description": "Quantity to purchase."},
                "customer_email": {"type": "string", "description": "Buyer email for order receipt."},
                "customer_phone": {"type": "string", "description": "Buyer phone number."}
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "simulate_payment",
        "description": "Execute a test-mode payment capture for an order on the Razorpay gateway.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The internal order ID or Razorpay order ID."},
                "payment_method": {"type": "string", "enum": ["card", "upi", "netbanking", "wallet"], "description": "Preferred payment method (defaults to upi)."}
            },
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "verify_payment",
        "description": "Cryptographically verify Razorpay HMAC-SHA256 signature to guarantee payment authenticity.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID."},
                "payment_id": {"type": "string", "description": "The Razorpay payment ID (e.g. pay_...)."},
                "signature": {"type": "string", "description": "The HMAC signature received from Razorpay."}
            },
            "required": ["order_id", "payment_id", "signature"]
        }
    },
    {
        "type": "function",
        "name": "get_order_status",
        "description": "Fetch live fulfillment, verification, and payment status for an existing order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The internal order ID or Razorpay order ID."}
            },
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "analyze_store_optimization",
        "description": "Audit product semantic discoverability for AI buyers and generate optimization recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to audit (optional). If omitted, audits the whole catalog."}
            },
            "required": []
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any], db: Session, razorpay_client: RazorpayClient) -> Dict[str, Any]:
    """Execute the requested tool with latency tracking and error isolation."""
    start_time = time.time()
    try:
        result = _route_tool(tool_name, arguments, db, razorpay_client)
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        result = {"error": str(e)}

    latency_ms = (time.time() - start_time) * 1000
    result["_latency_ms"] = round(latency_ms, 2)
    return result


def _route_tool(tool_name: str, args: Dict[str, Any], db: Session, rzp: RazorpayClient) -> Dict[str, Any]:
    if tool_name == "browse_catalog":
        category = args.get("category")
        sort_by = args.get("sort_by", "popularity")
        limit = int(args.get("limit", 10))
        items = catalog.browse_catalog_db(db, category=category, sort_by=sort_by, limit=limit)
        return {"count": len(items), "products": items}

    elif tool_name == "search_products":
        query_text = args.get("query", "")
        min_p = int(args["min_price"] * 100) if "min_price" in args and args["min_price"] is not None else None
        max_p = int(args["max_price"] * 100) if "max_price" in args and args["max_price"] is not None else None
        results = catalog.search_products_db(db, query_text=query_text, min_price=min_p, max_price=max_p)
        return {"count": len(results), "query": query_text, "results": results}

    elif tool_name == "get_product_details":
        p_id = args.get("product_id")
        item = catalog.get_product_by_id(db, p_id)
        if not item:
            return {"error": f"Product '{p_id}' not found in catalog."}
        return item

    elif tool_name == "compare_products":
        p_ids = args.get("product_ids", [])
        items = catalog.compare_products_db(db, p_ids)
        return {"compared_count": len(items), "products": items}

    elif tool_name == "check_availability":
        p_id = args.get("product_id")
        qty = int(args.get("quantity", 1))
        return catalog.check_availability_db(db, p_id, qty)

    elif tool_name == "create_razorpay_order":
        p_id = args.get("product_id")
        qty = int(args.get("quantity", 1))
        product = db.query(Product).filter(Product.id == p_id).first()
        if not product:
            return {"error": f"Product '{p_id}' not found."}
        if product.stock < qty:
            return {"error": f"Insufficient stock. Available: {product.stock}, Requested: {qty}"}

        amount_paise = int(product.price * qty)
        rzp_order = rzp.create_order(
            amount_paise=amount_paise,
            currency="INR",
            notes={"product_name": product.name, "quantity": qty}
        )

        new_order = Order(
            razorpay_order_id=rzp_order["id"],
            product_id=product.id,
            quantity=qty,
            amount=amount_paise,
            currency="INR",
            status="created",
            customer_email=args.get("customer_email", "buyer@example.com"),
            customer_phone=args.get("customer_phone", "+919876543210")
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {
            "order_id": new_order.id,
            "razorpay_order_id": new_order.razorpay_order_id,
            "product_name": product.name,
            "quantity": qty,
            "amount_inr": amount_paise / 100,
            "currency": "INR",
            "status": new_order.status
        }

    elif tool_name == "simulate_payment":
        order_key = str(args.get("order_id", ""))
        order = db.query(Order).filter(
            (Order.razorpay_order_id == order_key) | (Order.id == int(order_key) if order_key.isdigit() else False)
        ).first()

        if not order:
            return {"error": f"Order '{order_key}' not found."}

        method = args.get("payment_method", "upi")
        sim_data = rzp.simulate_test_payment(order.razorpay_order_id, method=method)

        payment = Payment(
            order_id=order.id,
            razorpay_payment_id=sim_data["payment_id"],
            razorpay_order_id=order.razorpay_order_id,
            razorpay_signature=sim_data["signature"],
            amount=order.amount,
            method=method,
            status="captured",
            signature_verified=True
        )
        db.add(payment)
        order.status = "paid"

        # Decrement product stock
        if order.product:
            order.product.stock = max(0, order.product.stock - order.quantity)

        db.commit()

        return {
            "status": "success",
            "message": "Payment captured successfully on Razorpay Gateway.",
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "payment_id": payment.razorpay_payment_id,
            "signature": sim_data["signature"],
            "amount_paid_inr": order.amount / 100,
            "payment_method": method
        }

    elif tool_name == "verify_payment":
        order_key = str(args.get("order_id", ""))
        payment_id = args.get("payment_id", "")
        signature = args.get("signature", "")

        order = db.query(Order).filter(
            (Order.razorpay_order_id == order_key) | (Order.id == int(order_key) if order_key.isdigit() else False)
        ).first()

        if not order:
            return {"verified": False, "error": f"Order '{order_key}' not found."}

        is_valid = rzp.verify_payment_signature(
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=signature
        )

        if is_valid:
            order.status = "paid"
            pay_rec = db.query(Payment).filter(Payment.razorpay_payment_id == payment_id).first()
            if pay_rec:
                pay_rec.signature_verified = True
                pay_rec.status = "captured"
            db.commit()
            return {"verified": True, "message": "Cryptographic HMAC signature verified.", "order_status": "paid"}
        else:
            return {"verified": False, "error": "Invalid HMAC signature. Possible tampering detected."}

    elif tool_name == "get_order_status":
        order_key = str(args.get("order_id", ""))
        order = db.query(Order).filter(
            (Order.razorpay_order_id == order_key) | (Order.id == int(order_key) if order_key.isdigit() else False)
        ).first()

        if not order:
            return {"error": f"Order '{order_key}' not found."}

        pay_info = {
            "payment_id": order.payment.razorpay_payment_id if order.payment else None,
            "method": order.payment.method if order.payment else None,
            "verified": order.payment.signature_verified if order.payment else False,
        } if order.payment else None

        return {
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "product_id": order.product_id,
            "product_name": order.product.name if order.product else "",
            "quantity": order.quantity,
            "amount_inr": order.amount / 100,
            "status": order.status,
            "payment": pay_info,
            "created_at": str(order.created_at)
        }

    elif tool_name == "analyze_store_optimization":
        p_id = args.get("product_id")
        if p_id:
            product = db.query(Product).filter(Product.id == p_id).first()
            if not product:
                return {"error": f"Product '{p_id}' not found."}
            return calculate_discoverability_score(product)
        else:
            all_products = db.query(Product).filter(Product.is_active == True).all()
            from backend.optimizer import analyze_catalog_optimization
            return analyze_catalog_optimization(all_products)

    return {"error": f"Unknown tool name: '{tool_name}'"}
