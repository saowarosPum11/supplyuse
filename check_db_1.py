import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables:", tables)

# Check products data
try:
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    print(f"Products count: {len(products)}")
    for product in products:
        print(f"Product: {product}")
except Exception as e:
    print(f"Error reading products: {e}")

# Check table structure
try:
    c.execute("PRAGMA table_info(products)")
    columns = c.fetchall()
    print("Columns:", columns)
except Exception as e:
    print(f"Error reading table info: {e}")

conn.close()