# SupplyUse - Deploy Guide

## Railway Deployment

### ขั้นตอนการ Deploy:

1. **สร้าง GitHub Repository**
   - ไปที่ github.com
   - สร้าง repository ใหม่ชื่อ "supplyuse"
   - เลือก Public

2. **Upload โค้ด**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/[username]/supplyuse.git
   git push -u origin main
   ```

3. **Deploy บน Railway**
   - ไปที่ railway.app
   - Sign up ด้วย GitHub
   - คลิก "New Project"
   - เลือก "Deploy from GitHub repo"
   - เลือก repository "supplyuse"
   - Railway จะ deploy อัตโนมัติ

4. **ได้ URL**
   - หลัง deploy เสร็จจะได้ URL เช่น:
   - `https://supplyuse-production.up.railway.app`

### Login Info:
- Username: `admin`
- Password: `SupplyUse2024!`

### Features:
- ✅ ระบบจัดการสต๊อก
- ✅ รับเข้า/เบิกออกสินค้า
- ✅ รายงานและสถิติ
- ✅ สแกนบาร์โค้ด
- ✅ ระบบผู้ใช้งาน