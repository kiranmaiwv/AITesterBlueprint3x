"""Duplicate record checks."""


def test_customer_id_unique(db):
    cur = db.cursor()
    cur.execute(
        "SELECT customer_id, COUNT(*) c FROM customers "
        "GROUP BY customer_id HAVING c > 1"
    )
    dups = cur.fetchall()
    assert not dups, f"Duplicate customer_id values found: {dups}"


def test_customer_email_unique(db):
    # This test is expected to FIND a soft-duplicate email in the sample data,
    # demonstrating real QA value.
    cur = db.cursor()
    cur.execute(
        "SELECT email, COUNT(*) c FROM customers "
        "GROUP BY email HAVING c > 1"
    )
    dups = cur.fetchall()
    assert not dups, f"Duplicate email values found: {dups}"


def test_order_id_unique(db):
    cur = db.cursor()
    cur.execute(
        "SELECT order_id, COUNT(*) c FROM orders "
        "GROUP BY order_id HAVING c > 1"
    )
    dups = cur.fetchall()
    assert not dups, f"Duplicate order_id values found: {dups}"
