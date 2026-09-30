"""Unit tests for product catalog functions."""

from backend.catalog import (
    seed_catalog, browse_catalog_db, search_products_db,
    get_product_by_id, compare_products_db, check_availability_db,
    SEED_PRODUCTS,
)
from backend.models import Product


class TestSeedCatalog:
    def test_seeds_20_products(self, db_session):
        count = db_session.query(Product).count()
        assert count == 20

    def test_idempotent_seeding(self, db_session):
        added = seed_catalog(db_session)
        assert added == 0
        assert db_session.query(Product).count() == 20

    def test_seed_data_has_required_fields(self):
        for p in SEED_PRODUCTS:
            assert "id" in p
            assert "name" in p
            assert "price" in p
            assert isinstance(p["price"], int)
            assert p["price"] > 0


class TestBrowseCatalog:
    def test_returns_products(self, db_session):
        items = browse_catalog_db(db_session, limit=10)
        assert len(items) == 10

    def test_has_price_display(self, db_session):
        items = browse_catalog_db(db_session, limit=1)
        assert "₹" in items[0]["price_display"]

    def test_filter_by_category(self, db_session):
        items = browse_catalog_db(db_session, category="electronics")
        assert len(items) > 0
        for item in items:
            assert item["category"] == "electronics"

    def test_filter_by_gaming(self, db_session):
        items = browse_catalog_db(db_session, category="gaming")
        assert len(items) >= 3

    def test_sort_price_asc(self, db_session):
        items = browse_catalog_db(db_session, sort_by="price_asc", limit=20)
        prices = [i["price_paise"] for i in items]
        assert prices == sorted(prices)

    def test_sort_price_desc(self, db_session):
        items = browse_catalog_db(db_session, sort_by="price_desc", limit=20)
        prices = [i["price_paise"] for i in items]
        assert prices == sorted(prices, reverse=True)

    def test_limit(self, db_session):
        items = browse_catalog_db(db_session, limit=3)
        assert len(items) == 3


class TestSearchProducts:
    def test_search_by_name(self, db_session):
        results = search_products_db(db_session, query_text="earbuds")
        assert len(results) > 0
        assert any("Sony" in r["name"] for r in results)

    def test_search_by_brand(self, db_session):
        results = search_products_db(db_session, query_text="JBL")
        assert len(results) > 0

    def test_search_with_max_price(self, db_session):
        results = search_products_db(db_session, query_text="speaker", max_price=1000000)
        for r in results:
            assert r["price_paise"] <= 1000000

    def test_search_no_results(self, db_session):
        results = search_products_db(db_session, query_text="xyznonexistent123")
        assert len(results) == 0

    def test_search_by_category_keyword(self, db_session):
        results = search_products_db(db_session, query_text="gaming")
        assert len(results) > 0


class TestGetProductById:
    def test_found(self, db_session):
        p = get_product_by_id(db_session, "ELEC001")
        assert p is not None
        assert p["id"] == "ELEC001"
        assert p["brand"] == "Sony"

    def test_not_found(self, db_session):
        p = get_product_by_id(db_session, "NONEXISTENT")
        assert p is None

    def test_has_specs(self, db_session):
        p = get_product_by_id(db_session, "ELEC002")
        assert "specs" in p
        assert isinstance(p["specs"], dict)
        assert len(p["specs"]) > 0


class TestCompareProducts:
    def test_compare_two(self, db_session):
        items = compare_products_db(db_session, ["ELEC001", "ELEC004"])
        assert len(items) == 2
        ids = {i["id"] for i in items}
        assert ids == {"ELEC001", "ELEC004"}

    def test_compare_three(self, db_session):
        items = compare_products_db(db_session, ["BOOK001", "BOOK002", "BOOK003"])
        assert len(items) == 3

    def test_compare_empty_list(self, db_session):
        items = compare_products_db(db_session, [])
        assert len(items) == 0


class TestCheckAvailability:
    def test_in_stock(self, db_session):
        result = check_availability_db(db_session, "ELEC001", quantity=2)
        assert result["available"] is True
        assert result["requested_quantity"] == 2
        assert "business days" in result["estimated_delivery"]

    def test_out_of_stock(self, db_session):
        result = check_availability_db(db_session, "ELEC001", quantity=99999)
        assert result["available"] is False

    def test_not_found(self, db_session):
        result = check_availability_db(db_session, "DOESNOTEXIST")
        assert result["available"] is False
        assert "error" in result
