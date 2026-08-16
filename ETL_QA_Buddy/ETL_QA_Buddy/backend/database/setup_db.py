"""
setup_db.py — Standalone script to create and populate the ETL QA Buddy SQLite database.

Run with:  python setup_db.py

This creates `etl_qa.db` in the same directory with 5 realistic ETL tables and
sample data. A few intentional data-quality issues are baked in so that some QA
tests fail naturally (demonstrating real QA value):

  * 2 customers with NULL phone
  * 1 soft-duplicate email (same email used by two customers)
  * 1 order with total_amount = 0.0 (suspicious value)
  * 1 ETL log entry with status='partial' and rows_extracted != rows_loaded
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etl_qa.db")


SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS etl_log;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    phone       TEXT,
    country     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    is_active   INTEGER NOT NULL
);

CREATE TABLE products (
    product_id     INTEGER PRIMARY KEY,
    product_name   TEXT NOT NULL,
    category       TEXT NOT NULL,
    unit_price     REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    supplier_id    INTEGER
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date   TEXT NOT NULL,
    status       TEXT NOT NULL,
    total_amount REAL NOT NULL
);

CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE etl_log (
    log_id         INTEGER PRIMARY KEY,
    pipeline_name  TEXT NOT NULL,
    run_date       TEXT NOT NULL,
    rows_extracted INTEGER,
    rows_loaded    INTEGER,
    status         TEXT NOT NULL,
    error_message  TEXT
);
"""


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

# 20 customers. Note the intentional issues:
#   - customer 7 and 14 have NULL phone
#   - customer 20 reuses customer 1's email (soft duplicate)
CUSTOMERS = [
    (1,  "Alice",   "Johnson",   "alice.johnson@example.com",   "+1-202-555-0101", "USA",     "2023-01-15", 1),
    (2,  "Bob",     "Smith",     "bob.smith@example.com",       "+1-202-555-0102", "USA",     "2023-01-18", 1),
    (3,  "Carla",   "Diaz",      "carla.diaz@example.com",      "+34-91-555-0103", "Spain",   "2023-02-02", 1),
    (4,  "David",   "Nguyen",    "david.nguyen@example.com",    "+84-24-555-0104", "Vietnam", "2023-02-10", 1),
    (5,  "Emma",    "Brown",     "emma.brown@example.com",      "+44-20-555-0105", "UK",      "2023-02-21", 1),
    (6,  "Frank",   "Meyer",     "frank.meyer@example.com",     "+49-30-555-0106", "Germany", "2023-03-01", 0),
    (7,  "Grace",   "Lee",       "grace.lee@example.com",       None,              "Canada",  "2023-03-11", 1),
    (8,  "Hiro",    "Tanaka",    "hiro.tanaka@example.com",     "+81-3-555-0108",  "Japan",   "2023-03-19", 1),
    (9,  "Isabel",  "Rossi",     "isabel.rossi@example.com",    "+39-06-555-0109", "Italy",   "2023-04-02", 1),
    (10, "Jack",    "Wilson",    "jack.wilson@example.com",     "+61-2-555-0110",  "Australia","2023-04-15",1),
    (11, "Karen",   "Miller",    "karen.miller@example.com",    "+1-202-555-0111", "USA",     "2023-04-28", 1),
    (12, "Liam",    "O'Brien",   "liam.obrien@example.com",     "+353-1-555-0112", "Ireland", "2023-05-05", 1),
    (13, "Maria",   "Garcia",    "maria.garcia@example.com",    "+52-55-555-0113", "Mexico",  "2023-05-14", 0),
    (14, "Noah",    "Schmidt",   "noah.schmidt@example.com",    None,              "Germany", "2023-05-27", 1),
    (15, "Olivia",  "Martin",    "olivia.martin@example.com",   "+33-1-555-0115",  "France",  "2023-06-03", 1),
    (16, "Paul",    "Anderson",  "paul.anderson@example.com",   "+1-202-555-0116", "USA",     "2023-06-18", 1),
    (17, "Qi",      "Chen",      "qi.chen@example.com",         "+86-10-555-0117", "China",   "2023-07-01", 1),
    (18, "Rachel",  "Green",     "rachel.green@example.com",    "+1-202-555-0118", "USA",     "2023-07-12", 1),
    (19, "Sven",    "Larsson",   "sven.larsson@example.com",    "+46-8-555-0119",  "Sweden",  "2023-07-25", 1),
    # Soft-duplicate email: reuses alice.johnson@example.com
    (20, "Tina",    "Alvarez",   "alice.johnson@example.com",   "+1-202-555-0120", "USA",     "2023-08-01", 1),
]

# 15 products
PRODUCTS = [
    (1,  "Wireless Mouse",        "Electronics", 24.99,  150, 101),
    (2,  "Mechanical Keyboard",   "Electronics", 79.99,  80,  101),
    (3,  "USB-C Hub",             "Electronics", 39.50,  60,  102),
    (4,  "27-inch Monitor",       "Electronics", 229.00, 25,  103),
    (5,  "Laptop Stand",          "Accessories", 34.95,  120, 104),
    (6,  "Noise-Cancel Headset",  "Audio",       149.99, 40,  105),
    (7,  "Webcam 1080p",          "Electronics", 59.99,  70,  102),
    (8,  "Desk Lamp LED",         "Home Office", 27.49,  90,  106),
    (9,  "Ergonomic Chair",       "Furniture",   319.00, 15,  107),
    (10, "Standing Desk",         "Furniture",   459.00, 10,  107),
    (11, "Notebook A5",           "Stationery",  6.99,   500, 108),
    (12, "Gel Pen Pack",          "Stationery",  4.25,   800, 108),
    (13, "External SSD 1TB",      "Storage",     109.99, 55,  103),
    (14, "HDMI Cable 2m",         "Accessories", 9.99,   300, 104),
    (15, "Bluetooth Speaker",     "Audio",       45.00,  65,  105),
]

# 30 orders. Note: order 13 has total_amount = 0.0 (suspicious value).
ORDERS = [
    (1,  1,  "2023-08-05", "delivered", 104.98),
    (2,  2,  "2023-08-06", "shipped",   229.00),
    (3,  3,  "2023-08-07", "delivered", 84.49),
    (4,  4,  "2023-08-08", "pending",   149.99),
    (5,  5,  "2023-08-09", "delivered", 39.50),
    (6,  6,  "2023-08-10", "cancelled", 79.99),
    (7,  7,  "2023-08-11", "delivered", 319.00),
    (8,  8,  "2023-08-12", "shipped",   64.98),
    (9,  9,  "2023-08-13", "delivered", 229.00),
    (10, 10, "2023-08-14", "pending",   109.99),
    (11, 11, "2023-08-15", "delivered", 24.99),
    (12, 12, "2023-08-16", "shipped",   459.00),
    (13, 13, "2023-08-17", "pending",   0.0),     # suspicious zero total
    (14, 14, "2023-08-18", "delivered", 54.98),
    (15, 15, "2023-08-19", "delivered", 149.99),
    (16, 16, "2023-08-20", "shipped",   34.95),
    (17, 17, "2023-08-21", "delivered", 219.98),
    (18, 18, "2023-08-22", "pending",   45.00),
    (19, 19, "2023-08-23", "delivered", 109.99),
    (20, 1,  "2023-08-24", "delivered", 79.99),
    (21, 2,  "2023-08-25", "shipped",   27.49),
    (22, 3,  "2023-08-26", "delivered", 13.24),
    (23, 5,  "2023-08-27", "cancelled", 229.00),
    (24, 8,  "2023-08-28", "delivered", 149.99),
    (25, 10, "2023-08-29", "shipped",   319.00),
    (26, 11, "2023-08-30", "delivered", 59.99),
    (27, 15, "2023-08-31", "delivered", 39.50),
    (28, 16, "2023-09-01", "pending",   459.00),
    (29, 18, "2023-09-02", "delivered", 24.99),
    (30, 19, "2023-09-03", "shipped",   109.99),
]

# 50 order_items referencing valid orders and products.
ORDER_ITEMS = [
    (1,  1,  1,  2, 24.99),
    (2,  1,  5,  1, 34.95),
    (3,  2,  4,  1, 229.00),
    (4,  3,  3,  1, 39.50),
    (5,  3,  5,  1, 34.95),
    (6,  4,  6,  1, 149.99),
    (7,  5,  3,  1, 39.50),
    (8,  6,  2,  1, 79.99),
    (9,  7,  9,  1, 319.00),
    (10, 8,  7,  1, 59.99),
    (11, 8,  11, 1, 6.99),
    (12, 9,  4,  1, 229.00),
    (13, 10, 13, 1, 109.99),
    (14, 11, 1,  1, 24.99),
    (15, 12, 10, 1, 459.00),
    (16, 13, 12, 1, 4.25),
    (17, 14, 8,  2, 27.49),
    (18, 15, 6,  1, 149.99),
    (19, 16, 5,  1, 34.95),
    (20, 17, 4,  1, 229.00),
    (21, 18, 15, 1, 45.00),
    (22, 19, 13, 1, 109.99),
    (23, 20, 2,  1, 79.99),
    (24, 21, 8,  1, 27.49),
    (25, 22, 12, 2, 4.25),
    (26, 22, 11, 1, 6.99),
    (27, 23, 4,  1, 229.00),
    (28, 24, 6,  1, 149.99),
    (29, 25, 9,  1, 319.00),
    (30, 26, 7,  1, 59.99),
    (31, 27, 3,  1, 39.50),
    (32, 28, 10, 1, 459.00),
    (33, 29, 1,  1, 24.99),
    (34, 30, 13, 1, 109.99),
    (35, 1,  11, 1, 6.99),
    (36, 2,  14, 1, 9.99),
    (37, 4,  15, 1, 45.00),
    (38, 5,  12, 2, 4.25),
    (39, 7,  8,  1, 27.49),
    (40, 9,  5,  1, 34.95),
    (41, 10, 14, 1, 9.99),
    (42, 12, 9,  1, 319.00),
    (43, 15, 3,  1, 39.50),
    (44, 17, 1,  1, 24.99),
    (45, 19, 11, 2, 6.99),
    (46, 21, 12, 1, 4.25),
    (47, 24, 7,  1, 59.99),
    (48, 26, 14, 1, 9.99),
    (49, 28, 5,  1, 34.95),
    (50, 30, 15, 1, 45.00),
]

# 10 ETL log rows. Note: log 6 is 'partial' with rows_extracted != rows_loaded.
ETL_LOG = [
    (1,  "customers_ingest", "2023-09-01", 20, 20, "success", None),
    (2,  "products_ingest",  "2023-09-01", 15, 15, "success", None),
    (3,  "orders_ingest",    "2023-09-01", 30, 30, "success", None),
    (4,  "order_items_ingest","2023-09-01", 50, 50, "success", None),
    (5,  "etl_log_rollup",   "2023-09-01", 10, 10, "success", None),
    (6,  "daily_sales_agg",  "2023-09-02", 100, 87, "partial", "13 rows skipped due to null customer_id"),
    (7,  "customers_ingest", "2023-09-02", 22, 22, "success", None),
    (8,  "products_ingest",  "2023-09-02", 15, 15, "success", None),
    (9,  "orders_ingest",    "2023-09-02", 32, 32, "success", None),
    (10, "inventory_sync",   "2023-09-02", 15, 15, "success", None),
]


def create_database(db_path: str = DB_PATH) -> None:
    """Create the schema and populate all tables. Overwrites any existing DB."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(SCHEMA)

        cur.executemany(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)", CUSTOMERS
        )
        cur.executemany(
            "INSERT INTO products VALUES (?,?,?,?,?,?)", PRODUCTS
        )
        cur.executemany(
            "INSERT INTO orders VALUES (?,?,?,?,?)", ORDERS
        )
        cur.executemany(
            "INSERT INTO order_items VALUES (?,?,?,?,?)", ORDER_ITEMS
        )
        cur.executemany(
            "INSERT INTO etl_log VALUES (?,?,?,?,?,?,?)", ETL_LOG
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
    print(f"Database created and populated at: {DB_PATH}")
    print("Tables: customers(20), products(15), orders(30), order_items(50), etl_log(10)")
    print("Intentional data-quality issues included for QA demonstration.")
