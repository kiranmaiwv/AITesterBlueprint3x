"""Foreign-key / referential integrity checks."""


def test_order_customer_fk(db):
    cur = db.cursor()
    cur.execute(
        "SELECT o.order_id FROM orders o "
        "LEFT JOIN customers c ON o.customer_id = c.customer_id "
        "WHERE c.customer_id IS NULL"
    )
    orphans = [r[0] for r in cur.fetchall()]
    assert not orphans, f"Orders referencing missing customers: {orphans}"


def test_order_item_order_fk(db):
    cur = db.cursor()
    cur.execute(
        "SELECT oi.item_id FROM order_items oi "
        "LEFT JOIN orders o ON oi.order_id = o.order_id "
        "WHERE o.order_id IS NULL"
    )
    orphans = [r[0] for r in cur.fetchall()]
    assert not orphans, f"Order items referencing missing orders: {orphans}"


def test_order_item_product_fk(db):
    cur = db.cursor()
    cur.execute(
        "SELECT oi.item_id FROM order_items oi "
        "LEFT JOIN products p ON oi.product_id = p.product_id "
        "WHERE p.product_id IS NULL"
    )
    orphans = [r[0] for r in cur.fetchall()]
    assert not orphans, f"Order items referencing missing products: {orphans}"
