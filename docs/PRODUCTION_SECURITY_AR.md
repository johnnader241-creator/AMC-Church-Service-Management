# أمان النسخة Production V1.7

## ما تم تأمينه
- كل الطلبات غير العامة تحتاج جلسة دخول.
- كل POST/PUT/PATCH/DELETE يحتاج CSRF token.
- تسجيل الخروج أصبح POST بدل GET.
- كل الشاشات الإدارية تعتمد على Role/Permission/Service Scope الموجودة في النظام.
- صفحات قاعدة البيانات، المهملات، Excel والمركز الإداري محمية لـSuper Admin والصلاحيات المرتبطة بها.
- OTP لا يعرض الرمز في الإنتاج. يجب ربط مزود إرسال فعلي قبل تفعيل شاشات OTP المطلوبة.
- Cookies: Secure في الإنتاج، HttpOnly، SameSite=Lax.
- HSTS وX-Frame-Options وnosniff وReferrer-Policy وPermissions-Policy مفعلة في الإنتاج.
- لا يوجد Sign Up عام؛ إنشاء المستخدمين من مركز التحكم فقط.
- كلمات مرور المستخدمين الجدد: 12 حرفًا على الأقل في الإنتاج.
- قاعدة PostgreSQL لا يجب نشر منفذها للعامة؛ التطبيق فقط يصل إليها عبر DATABASE_URL.

## قبل فتح النظام للعامة
1. ضع SECRET_KEY عشوائيًا وقويًا (Render generateValue مناسب).
2. ضع BOOTSTRAP_ADMIN_PASSWORD قويًا ولا تحفظه في Git.
3. بعد أول دخول، أنشئ حسابات المستخدمين من مركز التحكم ولا تشارك حساب Super Admin.
4. لا تفعل OTP_REQUIRED في الإنتاج قبل توصيل SMS/Email/Auth provider فعلي.
5. لا تضع DATABASE_URL في المستودع.
6. استخدم HTTPS فقط.
