# قاعدة البيانات للإنتاج / Online

النظام الآن مصمم ليعمل محليًا بـ SQLite، وعند النشر Online بـ PostgreSQL.

## لماذا PostgreSQL؟
- قاعدة بيانات مركزية مشتركة بين كل الموبايلات وأجهزة الكمبيوتر.
- مناسبة للتشغيل الدائم والاتصالات المتزامنة.
- البيانات لا تعتمد على بقاء جهاز الكمبيوتر الشخصي مفتوحًا.

## المتغيرات الأساسية
- `APP_ENV=production`
- `SECRET_KEY` قيمة عشوائية قوية.
- `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`

## Docker محلي/سيرفر
1. انسخ `.env.example` إلى `.env`.
2. ضع `POSTGRES_PASSWORD` و `SECRET_KEY` قويين.
3. شغّل `docker compose up -d --build`.
4. راقب `docker compose ps` حتى تصبح قاعدة البيانات healthy.
5. يمكن فحص الاتصال بـ `python scripts/db_check.py` داخل بيئة التطبيق.

## نقل قاعدة SQLite الحالية
إذا عندك ملف `data/church_service.db` يحتوي على بيانات فعلية، لا تمسحه.
استخدم:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite data/church_service.db \
  --postgres "postgresql+psycopg://USER:PASSWORD@HOST:5432/church_service"
```

السكريبت يوقف العملية عند وجود تعارض Primary Key بدل الكتابة فوق بيانات موجودة.

## ملاحظة مهمة
في الإنتاج لا تعتمد على `create_all()` كآلية ترقية schema مستقبلية. عند بدء التطوير على schema بعد الإطلاق، نضيف Alembic migrations حتى تكون كل ترقية قابلة للتتبع والرجوع.
