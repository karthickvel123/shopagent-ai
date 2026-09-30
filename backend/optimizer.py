"""AI-discoverability scoring and optimization engine for merchant products."""

from typing import Dict, Any, List
from backend.models import Product


def calculate_discoverability_score(product: Product) -> Dict[str, Any]:
    """Calculate AI-discoverability score (0-100) and provide concrete recommendations."""
    score = 100.0
    recommendations: List[str] = []
    strengths: List[str] = []

    # 1. Description depth
    desc = product.description or ""
    if len(desc) < 40:
        score -= 25.0
        recommendations.append("Description is under 40 characters. AI agents need detailed semantic descriptions to match natural queries.")
    elif len(desc) < 80:
        score -= 10.0
        recommendations.append("Expand description to 100+ characters with key use-cases and problem-solving details.")
    else:
        strengths.append("Thorough descriptive text enables rich natural language indexing.")

    # 2. AI Tags
    tags = product.ai_tags or []
    if not tags:
        score -= 25.0
        recommendations.append("No AI tags provided. Add 4-8 intent-based tags (e.g., 'running', 'gaming', 'fast charging').")
    elif len(tags) < 3:
        score -= 10.0
        recommendations.append(f"Only {len(tags)} tags provided. Increase to at least 5 tags for broader retrieval surface.")
    else:
        strengths.append(f"Well-tagged ({len(tags)} semantic tags) for faceted AI buyer retrieval.")

    # 3. Structured Specs
    specs = product.specs or {}
    if not specs or len(specs) < 2:
        score -= 20.0
        recommendations.append("Missing structured specifications. Autonomous agents evaluate technical parameters (battery, dimensions, ports).")
    else:
        strengths.append(f"Structured specs ({len(specs)} parameters) allow precise technical comparisons.")

    # 4. Brand and Category
    if not product.brand:
        score -= 10.0
        recommendations.append("Specify brand name to capture high-intent brand-specific shopper searches.")
    else:
        strengths.append(f"Brand verified: {product.brand}")

    # 5. Pricing and Stock
    if product.stock <= 0:
        score -= 15.0
        recommendations.append("Stock is 0. Out-of-stock items are penalized in autonomous buyer recommendations.")
    elif product.stock < 5:
        recommendations.append("Low inventory may cause agents to deprioritize in bulk or multi-item purchases.")

    final_score = max(10.0, min(100.0, round(score, 1)))

    return {
        "product_id": product.id,
        "product_name": product.name,
        "discoverability_score": final_score,
        "category": product.category,
        "strengths": strengths,
        "recommendations": recommendations,
        "readiness_tier": (
            "Agent-Ready (Tier 1)" if final_score >= 85
            else "Optimized (Tier 2)" if final_score >= 70
            else "Needs Enhancement (Tier 3)"
        ),
    }


def analyze_catalog_optimization(products: List[Product]) -> Dict[str, Any]:
    """Aggregate discoverability metrics across an entire merchant catalog."""
    if not products:
        return {
            "average_score": 0.0,
            "total_products": 0,
            "tier_distribution": {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0},
            "top_recommendations": ["Seed catalog with items to begin analysis."],
        }

    scores = []
    tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}
    all_recs = []

    for p in products:
        report = calculate_discoverability_score(p)
        scores.append(report["discoverability_score"])
        tier = report["readiness_tier"].split(" (")[0]
        if "Tier 1" in report["readiness_tier"]:
            tier_counts["Tier 1"] += 1
        elif "Tier 2" in report["readiness_tier"]:
            tier_counts["Tier 2"] += 1
        else:
            tier_counts["Tier 3"] += 1
        all_recs.extend(report["recommendations"])

    avg_score = round(sum(scores) / len(scores), 1)

    # Unique top recommendations
    from collections import Counter
    top_issues = [item for item, _ in Counter(all_recs).most_common(4)]

    return {
        "average_score": avg_score,
        "total_products": len(products),
        "tier_distribution": tier_counts,
        "top_recommendations": top_issues,
    }
