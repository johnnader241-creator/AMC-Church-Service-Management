# تشغيل النظام Online من أي شبكة

## المنصة المجهزة
الملف مجهز للنشر على Render باستخدام `render.yaml`.

## ماذا يحدث عند أول Deploy؟
- يتم إنشاء Web Service.
- يتم إنشاء PostgreSQL.
- `DATABASE_URL` يتم ربطه تلقائيًا بقاعدة البيانات.
- `SECRET_KEY` يتم توليده تلقائيًا.
- الاتصال يتم عبر HTTPS من Render.
- `/health` مستخدم كفحص صحة الخدمة.

## أول دخول
في أول إنشاء للبيانات، Render سيطلب قيمة `BOOTSTRAP_ADMIN_PASSWORD` لأن المتغير معرف بـ `sync: false`.
استخدم كلمة مرور قوية لا تقل عن 12 حرفًا.

اسم المستخدم الافتراضي: `admin` ويمكن تغييره من `BOOTSTRAP_ADMIN_USERNAME` قبل أول تشغيل.

> مهم: لا يوجد أي Password ثابت داخل الكود، ولا يتم تغيير كلمة مرور مستخدم موجود عند كل إعادة تشغيل.

## النشر
1. ارفع محتويات هذا المجلد إلى Repository على GitHub.
2. افتح Render واختر New → Blueprint.
3. اختر الـRepository الذي يحتوي على `render.yaml`.
4. عند إنشاء الـBlueprint، أدخل `BOOTSTRAP_ADMIN_PASSWORD`.
5. نفّذ Deploy.
6. بعد نجاح النشر، استخدم رابط `onrender.com` من أي هاتف/كمبيوتر وعلى أي شبكة.

## البيانات القديمة
إذا كانت لديك قاعدة SQLite محلية بها بيانات مهمة، لا تبدأ العمل على قاعدة Online جديدة قبل تنفيذ Migration إلى PostgreSQL.
استخدم `scripts/migrate_sqlite_to_postgres.py` بعد توفير `DATABASE_URL` الخاص بقاعدة PostgreSQL.

## ملاحظة عن الخطط
الـBlueprint مضبوط مبدئيًا على `free` لتقليل التكلفة. يمكن تغيير الخطة لاحقًا من Render إذا أردت تشغيلًا دائمًا بدون سكون أو موارد أعلى.