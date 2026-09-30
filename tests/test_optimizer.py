"""Unit tests for the AI-discoverability optimizer."""

from backend.optimizer import calculate_discoverability_score, analyze_catalog_optimization
from backend.models import Product


class TestDiscoverabilityScore:
    def test_well_formed_product(self, db_session):
        product = db_session.query(Product).filter(Product.id == "ELEC001").first()
        result = calculate_discoverability_score(product)
        assert result["discoverability_score"] >= 80
        assert result["product_id"] == "ELEC001"
        assert "Agent-Ready" in result["readiness_tier"]

    def test_product_with_good_tags(self, db_session):
        product = db_session.query(Product).filter(Product.id == "BOOK003").first()
        result = calculate_discoverability_score(product)
        assert result["discoverability_score"] > 70
        assert len(result["strengths"]) > 0

    def test_readiness_tier_labels(self, db_session):
        product = db_session.query(Product).filter(Product.id == "ELEC001").first()
        result = calculate_discoverability_score(product)
        assert result["readiness_tier"] in [
            "Agent-Ready (Tier 1)",
            "Optimized (Tier 2)",
            "Needs Enhancement (Tier 3)"
        ]


class TestCatalogOptimization:
    def test_full_catalog_analysis(self, db_session):
        products = db_session.query(Product).all()
        result = analyze_catalog_optimization(products)
        assert result["total_products"] == 20
        assert result["average_score"] > 0
        assert "Tier 1" in result["tier_distribution"]

    def test_empty_catalog(self, db_session):
        result = analyze_catalog_optimization([])
        assert result["total_products"] == 0
        assert result["average_score"] == 0.0
