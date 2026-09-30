"""Product catalog management with seed data for demo."""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models import Product

logger = logging.getLogger(__name__)

# ── 20 Realistic Indian E-Commerce Products ──────────────

SEED_PRODUCTS = [
    # ── Electronics ──
    {
        "id": "ELEC001",
        "name": "Sony WF-C500 Wireless Earbuds",
        "description": "Lightweight truly wireless earbuds with DSEE sound enhancement, 10-hour battery life, IPX4 water resistance. Deep bass with 5.8mm drivers.",
        "price": 349900,
        "category": "electronics",
        "brand": "Sony",
        "stock": 45,
        "rating": 4.3,
        "review_count": 1284,
        "specs": {"driver_size": "5.8mm", "battery": "10h", "bluetooth": "5.0", "water_resistance": "IPX4", "weight": "5.4g per bud"},
        "ai_tags": ["wireless earbuds", "bass", "sony", "bluetooth", "music", "workout"],
        "ai_discoverability_score": 0.92,
    },
    {
        "id": "ELEC002",
        "name": "Samsung Galaxy M35 5G",
        "description": "6.6-inch Super AMOLED display, Exynos 1380 processor, 50MP triple camera, 6000mAh battery with 25W fast charging. 8GB RAM, 128GB storage.",
        "price": 1599900,
        "category": "electronics",
        "brand": "Samsung",
        "stock": 30,
        "rating": 4.1,
        "review_count": 2156,
        "specs": {"display": "6.6\" Super AMOLED", "processor": "Exynos 1380", "ram": "8GB", "storage": "128GB", "battery": "6000mAh", "camera": "50MP+8MP+2MP"},
        "ai_tags": ["smartphone", "5g", "samsung", "amoled", "camera", "gaming"],
        "ai_discoverability_score": 0.88,
    },
    {
        "id": "ELEC003",
        "name": "Anker 735 GaN Charger 65W",
        "description": "Ultra-compact 65W 3-port GaN charger. Two USB-C and one USB-A port. Charges MacBook Air in 1.5 hours. Foldable plug for travel.",
        "price": 329900,
        "category": "electronics",
        "brand": "Anker",
        "stock": 80,
        "rating": 4.6,
        "review_count": 892,
        "specs": {"wattage": "65W", "ports": "2x USB-C, 1x USB-A", "technology": "GaN III", "weight": "112g"},
        "ai_tags": ["charger", "fast charging", "usb-c", "laptop charger", "travel", "gan"],
        "ai_discoverability_score": 0.85,
    },
    {
        "id": "ELEC004",
        "name": "JBL Flip 6 Portable Speaker",
        "description": "Powerful portable Bluetooth speaker with IP67 waterproof rating, 12-hour battery, JBL Pro Sound with separate tweeter. PartyBoost compatible.",
        "price": 899900,
        "category": "electronics",
        "brand": "JBL",
        "stock": 25,
        "rating": 4.5,
        "review_count": 3421,
        "specs": {"driver": "Racetrack-shaped", "battery": "12h", "waterproof": "IP67", "bluetooth": "5.1", "weight": "550g"},
        "ai_tags": ["bluetooth speaker", "portable", "waterproof", "outdoor", "party", "bass"],
        "ai_discoverability_score": 0.90,
    },
    {
        "id": "ELEC005",
        "name": "Fire-Boltt Phoenix Ultra Smartwatch",
        "description": "1.39-inch AMOLED display smartwatch with Bluetooth calling, 120+ sports modes, SpO2, heart rate & sleep tracking. 7-day battery life.",
        "price": 199900,
        "category": "electronics",
        "brand": "Fire-Boltt",
        "stock": 60,
        "rating": 4.0,
        "review_count": 5672,
        "specs": {"display": "1.39\" AMOLED", "battery": "7 days", "calling": "Bluetooth", "sports_modes": "120+", "sensors": "SpO2, HR, Sleep"},
        "ai_tags": ["smartwatch", "fitness tracker", "bluetooth calling", "amoled", "health"],
        "ai_discoverability_score": 0.82,
    },
    # ── Clothing ──
    {
        "id": "CLOTH001",
        "name": "U.S. Polo Assn. Classic Polo T-Shirt",
        "description": "Men's regular-fit cotton polo t-shirt with ribbed collar and sleeve cuffs. Embroidered logo on chest. Navy Blue color.",
        "price": 119900,
        "category": "clothing",
        "brand": "U.S. Polo Assn.",
        "stock": 100,
        "rating": 4.2,
        "review_count": 8934,
        "specs": {"material": "100% Cotton", "fit": "Regular", "collar": "Polo", "color": "Navy Blue"},
        "ai_tags": ["polo", "t-shirt", "cotton", "casual", "men", "branded"],
        "ai_discoverability_score": 0.80,
    },
    {
        "id": "CLOTH002",
        "name": "Levi's 511 Slim Fit Jeans",
        "description": "Iconic slim-fit jeans with stretch denim for comfort. Mid-rise waist, tapered leg. Rinse dark wash.",
        "price": 249900,
        "category": "clothing",
        "brand": "Levi's",
        "stock": 40,
        "rating": 4.4,
        "review_count": 6721,
        "specs": {"material": "98% Cotton, 2% Elastane", "fit": "Slim", "rise": "Mid", "wash": "Dark Rinse"},
        "ai_tags": ["jeans", "slim fit", "denim", "levis", "men", "casual"],
        "ai_discoverability_score": 0.84,
    },
    {
        "id": "CLOTH003",
        "name": "Puma RS-X Reinvention Sneakers",
        "description": "Retro-inspired chunky sneakers with RS cushioning technology. Breathable mesh upper, rubber outsole. Running shoes.",
        "price": 449900,
        "category": "clothing",
        "brand": "Puma",
        "stock": 20,
        "rating": 4.3,
        "review_count": 1567,
        "specs": {"material": "Mesh + Synthetic", "sole": "Rubber", "technology": "RS Cushioning", "type": "Chunky/Retro"},
        "ai_tags": ["sneakers", "running shoes", "puma", "chunky", "retro", "sports"],
        "ai_discoverability_score": 0.86,
    },
    {
        "id": "CLOTH004",
        "name": "Wildcraft HypaDry Rain Jacket",
        "description": "Waterproof rain jacket with HypaDry technology, sealed seams, adjustable hood. Packable into its own pocket. Lightweight 180g.",
        "price": 179900,
        "category": "clothing",
        "brand": "Wildcraft",
        "stock": 35,
        "rating": 4.1,
        "review_count": 2345,
        "specs": {"material": "Nylon with HypaDry", "waterproof": "10000mm", "weight": "180g", "packable": "Yes"},
        "ai_tags": ["rain jacket", "waterproof", "outdoor", "trekking", "packable", "monsoon"],
        "ai_discoverability_score": 0.83,
    },
    # ── Home ──
    {
        "id": "HOME001",
        "name": "Philips Domus LED Desk Lamp",
        "description": "Eye-comfort LED desk lamp with 4 brightness levels, color temperature adjustment (3000K-6500K), USB charging port, 60-min auto-off timer.",
        "price": 249900,
        "category": "home",
        "brand": "Philips",
        "stock": 50,
        "rating": 4.4,
        "review_count": 1876,
        "specs": {"wattage": "10W", "color_temp": "3000K-6500K", "brightness_levels": 4, "usb_port": "Yes", "timer": "60 min"},
        "ai_tags": ["desk lamp", "led", "study lamp", "eye care", "usb charging", "office"],
        "ai_discoverability_score": 0.89,
    },
    {
        "id": "HOME002",
        "name": "Spaces by Welspun 210 TC Bedsheet Set",
        "description": "King-size 210 TC cotton bedsheet set with 2 pillow covers. Floral print in teal. Fade-resistant, machine washable.",
        "price": 149900,
        "category": "home",
        "brand": "Spaces by Welspun",
        "stock": 70,
        "rating": 4.2,
        "review_count": 4532,
        "specs": {"size": "King (274x274cm)", "thread_count": "210 TC", "material": "100% Cotton", "pillow_covers": 2},
        "ai_tags": ["bedsheet", "cotton", "king size", "bedroom", "home decor"],
        "ai_discoverability_score": 0.81,
    },
    {
        "id": "HOME003",
        "name": "Bajaj Rex 500W Mixer Grinder",
        "description": "500W motor mixer grinder with 3 jars (liquidizing, dry grinding, chutney). Stainless steel blades, 3-speed control with pulse.",
        "price": 229900,
        "category": "home",
        "brand": "Bajaj",
        "stock": 55,
        "rating": 4.0,
        "review_count": 7892,
        "specs": {"wattage": "500W", "jars": 3, "blades": "Stainless Steel", "speed": "3 + Pulse"},
        "ai_tags": ["mixer grinder", "kitchen appliance", "bajaj", "blender", "cooking"],
        "ai_discoverability_score": 0.85,
    },
    {
        "id": "HOME004",
        "name": "Milton Thermosteel 1L Water Bottle",
        "description": "1-litre vacuum insulated stainless steel water bottle. Keeps hot for 24 hours, cold for 24 hours. Leak-proof lid, BPA-free.",
        "price": 89900,
        "category": "home",
        "brand": "Milton",
        "stock": 90,
        "rating": 4.3,
        "review_count": 12456,
        "specs": {"capacity": "1L", "material": "Stainless Steel", "insulation": "Vacuum", "hot_retention": "24h", "cold_retention": "24h"},
        "ai_tags": ["water bottle", "thermos", "steel", "insulated", "gym", "office"],
        "ai_discoverability_score": 0.87,
    },
    # ── Books ──
    {
        "id": "BOOK001",
        "name": "Clean Code by Robert C. Martin",
        "description": "A handbook of agile software craftsmanship. Learn to write clean, readable, maintainable code with practical examples and principles.",
        "price": 44900,
        "category": "books",
        "brand": "Pearson",
        "stock": 120,
        "rating": 4.7,
        "review_count": 23456,
        "specs": {"pages": 464, "language": "English", "format": "Paperback", "isbn": "978-0132350884"},
        "ai_tags": ["programming", "software engineering", "clean code", "agile", "coding", "best practices"],
        "ai_discoverability_score": 0.94,
    },
    {
        "id": "BOOK002",
        "name": "The Alchemist by Paulo Coelho",
        "description": "An enchanting novel about Santiago, a shepherd boy who travels from Spain to the Egyptian desert in search of his Personal Legend.",
        "price": 29900,
        "category": "books",
        "brand": "HarperOne",
        "stock": 200,
        "rating": 4.6,
        "review_count": 56789,
        "specs": {"pages": 208, "language": "English", "format": "Paperback", "genre": "Fiction / Philosophy"},
        "ai_tags": ["fiction", "novel", "philosophy", "self-discovery", "bestseller", "inspiration"],
        "ai_discoverability_score": 0.91,
    },
    {
        "id": "BOOK003",
        "name": "Atomic Habits by James Clear",
        "description": "Tiny changes, remarkable results. An easy and proven way to build good habits and break bad ones using the 4 Laws of Behavior Change.",
        "price": 39900,
        "category": "books",
        "brand": "Penguin",
        "stock": 150,
        "rating": 4.8,
        "review_count": 34567,
        "specs": {"pages": 320, "language": "English", "format": "Paperback", "genre": "Self-Help / Productivity"},
        "ai_tags": ["self-help", "habits", "productivity", "motivation", "bestseller", "psychology"],
        "ai_discoverability_score": 0.96,
    },
    # ── Gaming ──
    {
        "id": "GAME001",
        "name": "Xbox Wireless Controller — Carbon Black",
        "description": "Next-gen Xbox wireless controller with textured grip, hybrid D-pad, USB-C port, 3.5mm audio jack. Works with Xbox, PC, Android, iOS.",
        "price": 499900,
        "category": "gaming",
        "brand": "Microsoft",
        "stock": 15,
        "rating": 4.6,
        "review_count": 4567,
        "specs": {"connectivity": "Bluetooth + USB-C", "battery": "40h (AA)", "audio": "3.5mm Jack", "compatibility": "Xbox, PC, Android, iOS"},
        "ai_tags": ["gaming controller", "xbox", "wireless", "pc gaming", "console"],
        "ai_discoverability_score": 0.93,
    },
    {
        "id": "GAME002",
        "name": "Logitech G402 Hyperion Fury Gaming Mouse",
        "description": "Ultra-fast FPS gaming mouse with Fusion Engine sensor tracking at 500 IPS. 8 programmable buttons, 4000 DPI. Lightweight 108g.",
        "price": 249900,
        "category": "gaming",
        "brand": "Logitech",
        "stock": 35,
        "rating": 4.4,
        "review_count": 8901,
        "specs": {"sensor": "Fusion Engine", "dpi": "4000", "buttons": 8, "weight": "108g", "polling_rate": "1000Hz"},
        "ai_tags": ["gaming mouse", "fps", "logitech", "programmable", "esports"],
        "ai_discoverability_score": 0.89,
    },
    {
        "id": "GAME003",
        "name": "Cosmic Byte CB-GK-18 Mechanical Keyboard",
        "description": "Full-size mechanical keyboard with Outemu Blue switches, per-key RGB backlighting, N-key rollover, braided cable. Aluminum top plate.",
        "price": 299900,
        "category": "gaming",
        "brand": "Cosmic Byte",
        "stock": 40,
        "rating": 4.2,
        "review_count": 3456,
        "specs": {"switches": "Outemu Blue (Clicky)", "backlight": "Per-key RGB", "rollover": "N-Key", "frame": "Aluminum", "cable": "Braided USB"},
        "ai_tags": ["mechanical keyboard", "rgb", "gaming", "blue switches", "clicky", "typing"],
        "ai_discoverability_score": 0.85,
    },
    {
        "id": "GAME004",
        "name": "Ant Esports MP290 Gaming Mouse Pad XL",
        "description": "Extra-large gaming mouse pad (800×300mm) with micro-weave cloth surface, anti-slip rubber base, stitched edges. 3mm thickness.",
        "price": 49900,
        "category": "gaming",
        "brand": "Ant Esports",
        "stock": 75,
        "rating": 4.1,
        "review_count": 5678,
        "specs": {"size": "800×300×3mm", "surface": "Micro-weave Cloth", "base": "Anti-slip Rubber", "edges": "Stitched"},
        "ai_tags": ["mouse pad", "gaming", "desk mat", "xl", "anti-slip"],
        "ai_discoverability_score": 0.79,
    },
]


def _product_to_dict(product: Product) -> Dict[str, Any]:
    """Convert Product ORM instance to a clean dictionary."""
    if not product:
        return {}
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price_paise": product.price,
        "price_inr": product.price / 100,
        "price_display": f"₹{product.price / 100:,.0f}",
        "category": product.category,
        "brand": product.brand,
        "stock": product.stock,
        "rating": product.rating,
        "review_count": product.review_count,
        "specs": product.specs or {},
        "ai_tags": product.ai_tags or [],
        "ai_discoverability_score": product.ai_discoverability_score or 0.0,
    }


def seed_catalog(db: Session) -> int:
    """Insert seed products if not present. Returns count of newly inserted items."""
    added = 0
    for p_data in SEED_PRODUCTS:
        existing = db.query(Product).filter(Product.id == p_data["id"]).first()
        if not existing:
            product = Product(**p_data)
            db.add(product)
            added += 1
    if added > 0:
        db.commit()
        logger.info(f"Seeded {added} new products into catalog.")
    return added


def browse_catalog_db(
    db: Session,
    category: Optional[str] = None,
    sort_by: str = "popularity",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Browse catalog with filtering and sorting."""
    query = db.query(Product).filter(Product.is_active == True)
    if category:
        query = query.filter(Product.category == category.lower())

    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "popularity": Product.review_count.desc(),
        "newest": Product.created_at.desc(),
        "rating": Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort_by, Product.review_count.desc()))
    products = query.limit(limit).all()
    return [_product_to_dict(p) for p in products]


def search_products_db(
    db: Session,
    query_text: str,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search products by name, description, brand, or category."""
    q = db.query(Product).filter(Product.is_active == True)
    search_term = f"%{query_text.lower()}%"
    q = q.filter(
        or_(
            Product.name.ilike(search_term),
            Product.description.ilike(search_term),
            Product.brand.ilike(search_term),
            Product.category.ilike(search_term),
        )
    )

    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if category:
        q = q.filter(Product.category == category.lower())

    products = q.order_by(Product.rating.desc()).limit(20).all()
    return [_product_to_dict(p) for p in products]


def get_product_by_id(db: Session, product_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    return _product_to_dict(product) if product else None


def compare_products_db(db: Session, product_ids: List[str]) -> List[Dict[str, Any]]:
    """Compare multiple products by IDs."""
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    return [_product_to_dict(p) for p in products]


def check_availability_db(db: Session, product_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Check stock availability for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"available": False, "error": f"Product {product_id} not found"}

    in_stock = product.stock >= quantity
    return {
        "product_id": product_id,
        "product_name": product.name,
        "requested_quantity": quantity,
        "available_stock": product.stock,
        "available": in_stock,
        "estimated_delivery": "2-4 business days" if in_stock else "Out of stock",
    }
