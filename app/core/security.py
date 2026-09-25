from functools import wraps
from datetime import datetime, timedelta
from flask import session, redirect, url_for, abort, request
import hashlib, hmac, base64
from sqlalchemy import select
from ..db import get_db
from ..models import User, Role, Permission, RolePermission, UserPermissionOverride, Screen, RoleScreenSetting, OTPSession, SecuritySetting, AuditLog
import secrets, json

def now(): return datetime.utcnow()

def current_user(db):
    uid=session.get('user_id')
    if not uid: return None
    return db.get(User, uid)

def is_super(db, user):
    if not user: return False
    role=db.get(Role, user.role_id)
    return bool(role and role.role_code=='SUPER_ADMIN')

def effective_permission_codes(db, user):
    if not user: return set()
    role_perms = set(db.scalars(select(Permission.permission_code).join(RolePermission, RolePermission.permission_id==Permission.permission_id).where(RolePermission.role_id==user.role_id)).all())
    overrides = db.execute(select(Permission.permission_code, UserPermissionOverride.effect).join(UserPermissionOverride, UserPermissionOverride.permission_id==Permission.permission_id).where(UserPermissionOverride.user_id==user.user_id, UserPermissionOverride.is_active==True)).all()
    eff=set(role_perms)
    for code,effect in overrides:
        if effect=='DENY': eff.discard(code)
        elif effect=='ALLOW': eff.add(code)
    return eff

def has_perm(db, user, code):
    return is_super(db,user) or code in effective_permission_codes(db,user)

def scope_allows(db, user, service_id, on_date=None):
    if is_super(db,user): return True
    from ..models import UserServiceScope
    on_date=on_date or now().date()
    row=db.scalar(select(UserServiceScope).where(UserServiceScope.user_id==user.user_id,UserServiceScope.service_id==service_id,UserServiceScope.start_date<=on_date,UserServiceScope.end_date>=on_date))
    return row is not None

def accessible_services(db, user, on_date=None):
    if is_super(db,user):
        from ..models import Service
        return set(db.scalars(select(Service.service_id).where(Service.status=='ACTIVE')).all())
    from ..models import UserServiceScope
    on_date=on_date or now().date()
    return set(db.scalars(select(UserServiceScope.service_id).where(UserServiceScope.user_id==user.user_id,UserServiceScope.start_date<=on_date,UserServiceScope.end_date>=on_date)).all())

def screen_allowed(db,user,screen_code,need='VIEW'):
    if is_super(db,user): return True
    screen=db.scalar(select(Screen).where(Screen.screen_code==screen_code))
    if not screen: return False
    rs=db.get(RoleScreenSetting,(user.role_id,screen.screen_id))
    if not rs or not rs.show_screen: return False
    if need=='VIEW' and not rs.can_view: return False
    if need=='EDIT' and (not rs.can_view or not rs.can_edit): return False
    return True

def requires_otp(db,user,screen_code):
    if is_super(db,user): return False
    screen=db.scalar(select(Screen).where(Screen.screen_code==screen_code))
    rs=db.get(RoleScreenSetting,(user.role_id,screen.screen_id)) if screen else None
    return bool(rs and rs.otp_required)

def require_login(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        if 'user_id' not in session: return redirect(url_for('login', next=request.path))
        return fn(*a,**kw)
    return wrapper

def require_screen(screen_code,need='VIEW'):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            db=get_db(); user=current_user(db)
            try:
                if not user: return redirect(url_for('login'))
                if not screen_allowed(db,user,screen_code,need): abort(403)
                # OTP handshake is required after entering the screen.
                if requires_otp(db,user,screen_code):
                    allowed=session.get('otp_ok',{}).get(screen_code)
                    if not allowed: return redirect(url_for('otp_prompt',screen=screen_code,next=request.full_path))
                return fn(*a,**kw)
            finally: db.close()
        return wrapper
    return deco

def audit(db,user,action,entity_type,entity_id=None,old=None,new=None):
    log=AuditLog(log_id='LOG-'+secrets.token_hex(10),user_id=(user.user_id if user else None),action=action,entity_type=entity_type,entity_id=entity_id,old_value=old,new_value=new,timestamp=now())
    db.add(log)

def next_id(db, model, attr_name, prefix, digits=6):
    attr=getattr(model,attr_name)
    vals=db.scalars(select(attr)).all(); nums=[]
    for v in vals:
        if isinstance(v,str) and v.startswith(prefix) and v[len(prefix):].isdigit(): nums.append(int(v[len(prefix):]))
    n=max(nums,default=0)+1
    return f'{prefix}{n:0{digits}d}'

from .passwords import hash_password, verify_password_hash

def verify_password(user,password): return verify_password_hash(user.password_hash,password)

def issue_otp(db,user,screen_code):
    settings=db.get(SecuritySetting,1) or SecuritySetting(setting_id=1)
    # New OTP supersedes prior active OTPs for same user/screen.
    rows=db.scalars(select(OTPSession).where(OTPSession.user_id==user.user_id,OTPSession.screen_code==screen_code,OTPSession.status=='ISSUED')).all()
    for row in rows:
        row.status='EXPIRED'; row.superseded_at=now()
    code=f'{secrets.randbelow(1000000):06d}'
    s=OTPSession(otp_session_id=next_id(db,OTPSession,'otp_session_id','OTP',6),user_id=user.user_id,issued_by=user.user_id,screen_code=screen_code,otp_code=code,issued_at=now(),expires_at=now()+timedelta(seconds=settings.otp_validity_seconds),status='ISSUED',ip_address=request.remote_addr,user_agent=request.headers.get('User-Agent',''))
    db.add(s); db.flush(); return code