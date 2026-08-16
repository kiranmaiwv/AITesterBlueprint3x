"""Row count / completeness checks."""


def test_customers_min_rows(db):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM customers")
    count = cur.fetchone()[0]
    assert count >= 15, f"Expected at least 15 customers, found {count}"


def test_products_min_rows(db):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]
    assert count >= 10, f"Expected at least 10 products, found {count}"


def test_orders_have_items(db):
    cur = db.cursor()
    cur.execute(
        "SELECT o.order_id FROM orders o "
        "LEFT JOIN order_items oi ON o.order_id = oi.order_id "
        "WHERE oi.item_id IS NULL"
    )
    empty_orders = [r[0] for r in cur.fetchall()]
    assert not empty_orders, f"Orders with no line items: {empty_orders}"
