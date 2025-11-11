import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Drop and recreate table without total_price
c.execute('DROP TABLE IF EXISTS simple_document_items')

c.execute('''CREATE TABLE simple_document_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (document_id) REFERENCES simple_documents (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)''')

conn.commit()
conn.close()
print("แก้ไขตารางเรียบร้อย")