"""NULL value checks on critical columns."""


def test_customer_email_not_null(db):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM customers WHERE email IS NULL")
    null_count = cur.fetchone()[0]
    assert null_count == 0, f"Found {null_count} customers with NULL email"


def test_order_total_not_null(db):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE total_amount IS NULL")
    null_count = cur.fetchone()[0]
    assert null_count == 0, f"Found {null_count} orders with NULL total_amount"


def test_customer_country_not_null(db):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM customers WHERE country IS NULL")
    null_count = cur.fetchone()[0]
    assert null_count == 0, f"Found {null_count} customers with NULL country"
