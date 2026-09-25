from datetime import datetime, date
import os
from sqlalchemy import select, delete
from .core.passwords import hash_password
from .core.security import next_id
from .db import Base, engine, get_db
from .models import *

ROLES=[
 ('R001','SUPER_ADMIN','Super Admin'),
 ('R002','ADMIN','Admin'),
 ('R003','GENERAL_SECRETARY','General Secretary'),
 ('R004','SECRETARY','Secretary'),
 ('R005','ASSISTANT','Assistant'),
]
SCREENS=[
 ('SCR01','FOLLOWUP','الافتقاد',1),('SCR02','OPENINGS','الافتتاحيات',2),('SCR03','SERVANTS','الخدام',3),
 ('SCR04','EVALUATIONS','التقييمات',4),('SCR05','RESULTS','النتائج',5),('SCR06','CONTROL_CENTER','مركز التحكم',6)
]
PERMS=[
 ('P001','VIEW_FOLLOWUP','مشاهدة الافتقاد','FOLLOWUP'),('P002','EDIT_FOLLOWUP','تعديل الافتقاد','FOLLOWUP'),
 ('P003','VIEW_OPENINGS','مشاهدة الافتتاحيات','OPENINGS'),('P004','EDIT_OPENINGS','تعديل الافتتاحيات','OPENINGS'),('P005','MANAGE_OPENING_TRANSFERS','ترحيل/تبديل الافتتاحيات','OPENINGS'),
 ('P006','VIEW_SERVANTS','مشاهدة الخدام','SERVANTS'),('P007','EDIT_SERVANTS','تعديل الخدام','SERVANTS'),('P008','CREATE_SERVANTS','إضافة خدام','SERVANTS'),
 ('P009','VIEW_EVALUATIONS','مشاهدة التقييمات','EVALUATIONS'),('P010','EDIT_EVALUATIONS','تعديل التقييمات','EVALUATIONS'),('P011','EXCLUDE_EVALUATIONS','استبعاد تقييم','EVALUATIONS'),
 ('P012','VIEW_EVENTS','مشاهدة الأحداث','EVALUATIONS'),('P013','EDIT_EVENTS','تعديل الأحداث','EVALUATIONS'),
 ('P014','VIEW_TRANSFERS','مشاهدة النقلات','SERVANTS'),('P015','CREATE_TRANSFERS','إنشاء نقلة','SERVANTS'),('P016','APPROVE_DESTINATION_TRANSFER','اعتماد استقبال نقلة','SERVANTS'),('P017','APPROVE_SUPER_TRANSFER','اعتماد النقلة نهائيًا','CONTROL_CENTER'),('P018','CANCEL_TRANSFER','إلغاء النقلة','SERVANTS'),
 ('P019','VIEW_EXCUSES','مشاهدة الاعتذارات','EVALUATIONS'),('P020','CREATE_EXCUSES','إنشاء اعتذار','EVALUATIONS'),('P021','REVIEW_EXCUSES','مراجعة الاعتذارات','CONTROL_CENTER'),
 ('P022','VIEW_TRASH','مشاهدة المهملات','CONTROL_CENTER'),('P023','RESTORE_TRASH','استعادة المهملات','CONTROL_CENTER'),('P024','PERMANENT_DELETE','حذف نهائي','CONTROL_CENTER'),
 ('P025','RESET_USER_PASSWORD','إعادة تعيين كلمة مرور مستخدم','CONTROL_CENTER'),('P026','MANAGE_USER_SCOPES','إدارة نطاقات المستخدمين','CONTROL_CENTER'),('P027','MANAGE_OTP_SETTINGS','إدارة OTP','CONTROL_CENTER'),
 ('P028','VIEW_AUDIT_LOG','مشاهدة سجل التدقيق','CONTROL_CENTER'),('P029','EXPORT_AUDIT_LOG','تصدير سجل التدقيق','CONTROL_CENTER'),
 ('P030','REVIEW_EXCEL_CHANGES','مراجعة تغييرات Excel','CONTROL_CENTER'),('P031','APPLY_EXCEL_CHANGES','تطبيق تغييرات Excel','CONTROL_CENTER'),
 ('P032','VIEW_DATABASE_EXPLORER','استعراض قاعدة البيانات','CONTROL_CENTER'),('P033','EDIT_DATABASE_EXPLORER','تعديل قاعدة البيانات المسموحة','CONTROL_CENTER'),
 ('P034','CREATE_MEETINGS','إنشاء اجتماعات','EVALUATIONS'),]
DEFAULT_ALLOW={
 'SUPER_ADMIN': {'*'},
 'ADMIN': {'VIEW_SERVANTS','EDIT_SERVANTS','CREATE_SERVANTS','VIEW_EVALUATIONS','EDIT_EVALUATIONS','VIEW_EVENTS','EDIT_EVENTS','VIEW_OPENINGS','EDIT_OPENINGS','VIEW_TRANSFERS','CREATE_TRANSFERS','APPROVE_DESTINATION_TRANSFER','CANCEL_TRANSFER','VIEW_EXCUSES','CREATE_EXCUSES','REVIEW_EXCUSES','CREATE_MEETINGS'},
 'GENERAL_SECRETARY': {'VIEW_SERVANTS','VIEW_EVALUATIONS','VIEW_EVENTS','VIEW_OPENINGS','VIEW_TRANSFERS','VIEW_EXCUSES'},
 'SECRETARY': {'VIEW_OPENINGS','VIEW_SERVANTS','VIEW_EVALUATIONS','VIEW_EXCUSES','CREATE_EXCUSES','MANAGE_OPENING_TRANSFERS'},
 'ASSISTANT': {'VIEW_OPENINGS','VIEW_SERVANTS','VIEW_EVALUATIONS','MANAGE_OPENING_TRANSFERS'},
}

def seed():
    Base.metadata.create_all(engine)
    db=get_db()
    try:
        # roles/screens/perms
        rolemap={r.role_code:r for r in db.scalars(select(Role)).all()}
        for rid,code,name in ROLES:
            if code not in rolemap: db.add(Role(role_id=rid,role_code=code,display_name=name,is_system_role=True))
        db.flush()
        screenmap={s.screen_code:s for s in db.scalars(select(Screen)).all()}
        for sid,code,name,order in SCREENS:
            if code not in screenmap: db.add(Screen(screen_id=sid,screen_code=code,display_name=name,sort_order=order))
        db.flush(); screenmap={s.screen_code:s for s in db.scalars(select(Screen)).all()}
        existing={p.permission_code:p for p in db.scalars(select(Permission)).all()}
        for pid,code,name,screen_code in PERMS:
            if code not in existing: db.add(Permission(permission_id=pid,permission_code=code,permission_name=name,screen_id=screenmap[screen_code].screen_id))
        db.flush()
        rolemap={r.role_code:r for r in db.scalars(select(Role)).all()}; permmap={p.permission_code:p for p in db.scalars(select(Permission)).all()}
        # screen settings
        for rcode,role in rolemap.items():
            for s in screenmap.values():
                key=(role.role_id,s.screen_id)
                if not db.get(RoleScreenSetting,key):
                    is_super=rcode=='SUPER_ADMIN'; show=True if is_super else rcode in ('ADMIN','GENERAL_SECRETARY','SECRETARY','ASSISTANT')
                    view=True if is_super else (s.screen_code!='CONTROL_CENTER')
                    edit=is_super or (rcode=='ADMIN' and s.screen_code in ('SERVANTS','OPENINGS','EVALUATIONS'))
                    db.add(RoleScreenSetting(role_id=role.role_id,screen_id=s.screen_id,show_screen=show,can_view=view,can_edit=edit,otp_required=False))
        db.flush()
        # role permissions
        for rcode,allowed in DEFAULT_ALLOW.items():
            role=rolemap[rcode]
            if '*' in allowed: allowed=set(permmap)
            for code in allowed:
                if not db.get(RolePermission,(role.role_id,permmap[code].permission_id)):
                    db.add(RolePermission(role_id=role.role_id,permission_id=permmap[code].permission_id))
        if not db.get(SecuritySetting,1): db.add(SecuritySetting(setting_id=1,otp_validity_seconds=300,otp_max_attempts=5,otp_lock_seconds=300))
        # Bootstrap the first Super Admin from environment variables.
        # Never hard-code or overwrite a production password.
        bootstrap_username=os.getenv('BOOTSTRAP_ADMIN_USERNAME','admin').strip() or 'admin'
        bootstrap_email=os.getenv('BOOTSTRAP_ADMIN_EMAIL','admin@example.com').strip() or 'admin@example.com'
        bootstrap_password=os.getenv('BOOTSTRAP_ADMIN_PASSWORD','').strip()
        user=db.scalar(select(User).where(User.username==bootstrap_username))
        superrole=rolemap['SUPER_ADMIN']
        if not user:
            if os.getenv('APP_ENV','development').lower()=='production' and len(bootstrap_password)<12:
                raise RuntimeError('BOOTSTRAP_ADMIN_PASSWORD must be set and at least 12 characters in production.')
            if not bootstrap_password:
                bootstrap_password='local-dev-change-me'
            user=User(user_id=next_id(db,User,'user_id','U',3),username=bootstrap_username,email=bootstrap_email,password_hash=hash_password(bootstrap_password),role_id=superrole.role_id,is_active=True)
            db.add(user)
        else:
            # Preserve an existing password; only ensure the bootstrap account remains a Super Admin.
            user.role_id=superrole.role_id; user.is_active=True
        db.commit()
    finally: db.close()