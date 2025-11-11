import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Clear stock movements (IN type)
c.execute("DELETE FROM stock_movements WHERE type = 'IN'")

# Reset current stock to 0
c.execute("UPDATE products SET current_stock = 0")

conn.commit()
conn.close()

print("ล้างข้อมูลรับเข้าเรียบร้อยแล้ว")