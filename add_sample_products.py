import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Create products table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    barcode TEXT UNIQUE,
    unit TEXT,
    min_stock INTEGER DEFAULT 0,
    current_stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Sample products
products = [
    ('ปากกาลูกลื่น', 'PEN001', 'ด้าม', 10, 50),
    ('กระดาษ A4', 'PAPER001', 'รีม', 5, 20),
    ('ดินสอ HB', 'PENCIL001', 'แท่ง', 20, 100),
    ('ยางลบ', 'ERASER001', 'ก้อน', 15, 30),
    ('คลิป', 'CLIP001', 'กล่อง', 5, 25)
]

for product in products:
    try:
        c.execute('INSERT INTO products (name, barcode, unit, min_stock, current_stock) VALUES (?, ?, ?, ?, ?)', product)
        print(f"เพิ่ม {product[0]} เรียบร้อย")
    except sqlite3.IntegrityError:
        print(f"{product[0]} มีอยู่แล้ว")

conn.commit()
conn.close()
print("เพิ่มสินค้าตัวอย่างเรียบร้อย!")