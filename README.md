## به نام خدا

### پروژه پایانترم دیتابیس، رزرو بلیط مسابقات ورزشی

#### اعضای تیم:
- محمدرفیع فتاحی نیا (40323643)
- مهدی اسدیان (40317753)
- امیرحسین جعفری (40319423)
---
#### بخش بکند:
1. پیشنیاز ها را با دستور زیر نصب کنید:
``` bash
pip install -r requirements.txt
```
2. فایل .env خود را از .env.example بسازید
3. با دستور زیر، بکند را اجرا کنید:
``` bash
uvicorn app.main:app --reload
#or
uvicorn app.main:app --reload --port 8001
```

## 🎟️ سیستم رزرو و پرداخت (Reservations & Payments)

این بخش از سیستم وظیفه مدیریت رزروهای موقت (با مهلت ۱۰ دقیقه‌ای)، ثبت پرداخت‌ها و ارائه تاریخچه خریدهای کاربران را بر عهده دارد. تمامی کوئری‌های این بخش با **SQL خام (Raw SQL)** نوشته شده و از مکانیزم **Database Transactions** برای جلوگیری از تداخل داده‌ها (Race Conditions) و استفاده از قفل `FOR UPDATE` بهره می‌برند.

### ⚙️ متغیرهای محیطی مورد نیاز (.env)
برای اجرای این بخش، متغیرهای زیر باید در فایل `.env` تنظیم شده باشند:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/booking_db
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
