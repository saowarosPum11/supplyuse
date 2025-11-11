import sqlite3

# Test direct insert
conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

try:
    c.execute('INSERT INTO products (name, barcode, unit, min_stock) VALUES (?, ?, ?, ?)',
             ('ทดสอบสินค้า', '1234567890', 'ชิ้น', 10))
    conn.commit()
    print("Insert successful")
    
    # Check data
    c.execute('SELECT * FROM products')
    products = c.fetchall()
    print(f"Products: {products}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()