"""Business logic / transformation checks."""


def test_etl_log_no_failures(db):
    cur = db.cursor()
    cur.execute("SELECT log_id FROM etl_log WHERE status = 'failed'")
    failed = [r[0] for r in cur.fetchall()]
    assert not failed, f"ETL log entries with status='failed': {failed}"


def test_order_status_valid_values(db):
    valid = ("pending", "shipped", "delivered", "cancelled")
    cur = db.cursor()
    cur.execute("SELECT DISTINCT status FROM orders")
    statuses = [r[0] for r in cur.fetchall()]
    invalid = [s for s in statuses if s not in valid]
    assert not invalid, f"Invalid order status values: {invalid}"


def test_customer_active_flag_valid(db):
    cur = db.cursor()
    cur.execute("SELECT DISTINCT is_active FROM customers")
    flags = [r[0] for r in cur.fetchall()]
    invalid = [f for f in flags if f not in (0, 1)]
    assert not invalid, f"Invalid is_active values: {invalid}"
