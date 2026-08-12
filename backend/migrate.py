"""
Migration script: converts old products table (sizes + stock columns)
to new product_sizes table (per-size stock).

Run once: python migrate.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print("No existing database found — fresh start, no migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if applicable_measurements column exists in products table
    try:
        cur.execute("PRAGMA table_info(products)")
        cols = [row[1] for row in cur.fetchall()]
        if cols and 'applicable_measurements' not in cols:
            cur.execute("ALTER TABLE products ADD COLUMN applicable_measurements TEXT DEFAULT ''")
            conn.commit()
    except Exception as e:
        print(f"Migration check warning: {e}")

    # Check if product_sizes table already exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_sizes'")
    if cur.fetchone():
        print("product_sizes table already exists — schema up to date.")
        conn.close()
        return

    print("Starting migration...")

    # Read existing products
    cur.execute("PRAGMA table_info(products)")
    cols = [row[1] for row in cur.fetchall()]
    has_sizes = 'sizes' in cols
    has_stock = 'stock' in cols

    cur.execute("SELECT id, name, sizes, stock FROM products") if (has_sizes and has_stock) else None
    products = cur.fetchall() if (has_sizes and has_stock) else []

    # Create product_sizes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            size VARCHAR(30) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Migrate each product's sizes/stock into product_sizes rows
    for prod_id, prod_name, sizes_str, stock in products:
        sizes = [s.strip() for s in (sizes_str or '').split(',') if s.strip()]
        if not sizes:
            # No sizes — create a single "Free Size" row with full stock
            cur.execute(
                "INSERT INTO product_sizes (product_id, size, stock) VALUES (?, ?, ?)",
                (prod_id, 'Free Size', stock or 0)
            )
        else:
            # Distribute stock equally across sizes (best we can do without historic data)
            per_size = (stock or 0) // len(sizes)
            remainder = (stock or 0) % len(sizes)
            for i, size in enumerate(sizes):
                s = per_size + (1 if i == 0 else 0) * remainder
                cur.execute(
                    "INSERT INTO product_sizes (product_id, size, stock) VALUES (?, ?, ?)",
                    (prod_id, size, s)
                )

    # Remove old columns from products (SQLite doesn't support DROP COLUMN before 3.35)
    # We recreate the table without sizes/stock columns
    cur.execute("""
        CREATE TABLE products_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(100) NOT NULL,
            price FLOAT NOT NULL,
            image_filename VARCHAR(300) DEFAULT '',
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    cur.execute("""
        INSERT INTO products_new (id, name, category, price, image_filename, created_at, updated_at)
        SELECT id, name, category, price, image_filename, created_at, updated_at FROM products
    """)
    cur.execute("DROP TABLE products")
    cur.execute("ALTER TABLE products_new RENAME TO products")

    conn.commit()
    conn.close()
    print(f"Migration complete! Migrated {len(products)} products.")

if __name__ == '__main__':
    migrate()
