"""Data type / value-range validation checks."""


def test_product_price_positive(db):
    cur = db.cursor()
    cur.execute("SELECT product_id FROM products WHERE unit_price <= 0")
    bad = [r[0] for r in cur.fetchall()]
    assert not bad, f"Products with non-positive unit_price: {bad}"


def test_order_total_positive(db):
    # Expected to FAIL on the intentional order with total_amount = 0.0.
    cur = db.cursor()
    cur.execute("SELECT order_id FROM orders WHERE total_amount <= 0")
    bad = [r[0] for r in cur.fetchall()]
    assert not bad, f"Orders with non-positive total_amount: {bad}"


def test_stock_quantity_non_negative(db):
    cur = db.cursor()
    cur.execute("SELECT product_id FROM products WHERE stock_quantity < 0")
    bad = [r[0] for r in cur.fetchall()]
    assert not bad, f"Products with negative stock_quantity: {bad}"
