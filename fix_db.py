import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

# Add status column to documents table if it doesn't exist
try:
    c.execute('ALTER TABLE documents ADD COLUMN status TEXT DEFAULT "DRAFT"')
    print("เพิ่ม column status เรียบร้อย")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column status มีอยู่แล้ว")
    else:
        print(f"Error: {e}")

# Update existing records to have DRAFT status
c.execute('UPDATE documents SET status = "DRAFT" WHERE status IS NULL')

conn.commit()
conn.close()
print("แก้ไขฐานข้อมูลเรียบร้อย")