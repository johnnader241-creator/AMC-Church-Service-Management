# إدارة الخدمة — Fresh Start

نسخة كاملة من الصفر لنظام إدارة الخدمة، مبنية على PostgreSQL كـSource of Truth، مع دعم SQLite للتجربة المحلية.

## هوية النظام
- اسم النظام: **إدارة الخدمة**
- الاسم الفرعي: **مركز افا موسي لتطوير التربيه الكنسيه**
- الشعار: `static/logo.png`

## حساب Super Admin الأول
- Username: `johnnader`
- Password المحلي الافتراضي عند إنشاء قاعدة جديدة: `John@2026!`
- بعد أول دخول غيّر كلمة المرور من مركز التحكم.
- في Production/Online لا تستخدم كلمة المرور المحلية؛ اضبط `BOOTSTRAP_ADMIN_USERNAME` و`BOOTSTRAP_ADMIN_PASSWORD` في متغيرات البيئة.

كلمة المرور تخزن Hash داخل قاعدة البيانات.

## تشغيل Windows
1. فك الضغط في مجلد جديد.
2. شغّل `launch_fresh.bat`.
3. افتح `http://localhost:5000`.
4. سجل الدخول بالحساب أعلاه.

## PostgreSQL
ضع `DATABASE_URL` في `.env` إلى PostgreSQL، ثم شغّل:

`python scripts/bootstrap.py`

أو استخدم `docker-compose.yml`.

## الأقسام
- الافتقاد (مجهز ومؤجل)
- الافتتاحيات
- الخدام
- التقييمات
- النتائج
- الأحداث
- الاعتذارات
- النقلات
- مركز التحكم
- Database Explorer
- Trash
- Excel Review/Apply

## Excel
الملفات الستة داخل `excel/`.
Excel هو Reference / Recovery فقط؛ المسار المقصود هو:

`Excel → Review → Diff → Apply`

والـApply على قاعدة البيانات متاح لـSuper Admin فقط.

## ملاحظات أمنية
- غيّر `SECRET_KEY` في بيئة الإنتاج.
- اربط النظام بـHTTPS عند نشره على الإنترنت.
- OTP في وضع التطوير يظهر داخل شاشة التحقق؛ في الإنتاج اربطه بموفر OTP مناسب.
