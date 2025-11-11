import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS simple_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_no TEXT UNIQUE NOT NULL,
    doc_type TEXT NOT NULL,
    doc_date DATE NOT NULL,
    reference TEXT,
    notes TEXT,
    confirmed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS simple_document_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (document_id) REFERENCES simple_documents (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)''')

# Create sample documents
sample_docs = [
    ('RE2412001', 'RECEIVE', '2024-12-01', 'PO-001', 'รับเข้าสินค้าจากซัพพลายเออร์ A', 1),
    ('RE2412002', 'RECEIVE', '2024-12-02', 'PO-002', 'รับเข้าสินค้าจากซัพพลายเออร์ B', 0),
    ('IS2412001', 'ISSUE', '2024-12-03', 'REQ-001', 'เบิกสินค้าให้แผนกขาย', 1),
    ('IS2412002', 'ISSUE', '2024-12-04', 'REQ-002', 'เบิกสินค้าให้แผนกการตลาด', 0),
    ('RE2412003', 'RECEIVE', '2024-12-05', 'PO-003', 'รับเข้าสินค้าเพิ่มเติม', 0)
]

# Insert sample documents
for doc in sample_docs:
    try:
        c.execute('''INSERT INTO simple_documents (doc_no, doc_type, doc_date, reference, notes, confirmed)
                    VALUES (?, ?, ?, ?, ?, ?)''', doc)
    except sqlite3.IntegrityError:
        print(f"เอกสาร {doc[0]} มีอยู่แล้ว")

# Get product IDs
c.execute('SELECT id FROM products LIMIT 3')
product_ids = [row[0] for row in c.fetchall()]

if product_ids:
    # Get document IDs
    c.execute('SELECT id FROM simple_documents')
    doc_ids = [row[0] for row in c.fetchall()]
    
    # Create sample document items
    sample_items = []
    for i, doc_id in enumerate(doc_ids):
        for j, product_id in enumerate(product_ids[:2]):  # 2 items per document
            quantity = (i + 1) * (j + 1) * 5
            unit_price = 100 + (i * 10) + (j * 5)
            total_price = quantity * unit_price
            sample_items.append((doc_id, product_id, quantity, unit_price, total_price, f'หมายเหตุรายการ {j+1}'))
    
    # Insert sample items
    for item in sample_items:
        try:
            c.execute('''INSERT INTO simple_document_items (document_id, product_id, quantity, unit_price, total_price, notes)
                        VALUES (?, ?, ?, ?, ?, ?)''', item)
        except sqlite3.IntegrityError:
            pass

conn.commit()
conn.close()

print("สร้างข้อมูลตัวอย่างเรียบร้อย!")
print("- เอกสารรับเข้า: 3 เอกสาร")
print("- เอกสารเบิกออก: 2 เอกสาร")
print("- รายการสินค้าในแต่ละเอกสาร: 2 รายการ")