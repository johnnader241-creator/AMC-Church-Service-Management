from flask import render_template
from .security import is_super, effective_permission_codes
from ..db import get_db
from ..models import Screen, RoleScreenSetting
from sqlalchemy import select
from .i18n import AR_WEEKDAYS, AR_MONTHS, EVENT_AR, MEETING_STATUS_AR

def register(app):
    @app.context_processor
    def inject_ui():
        from flask import session
        
        db=get_db(); user=None; visible={}; perms=set()
        if session.get('user_id'):
            from ..models import User
            user=db.get(User,session['user_id'])
            perms=effective_permission_codes(db,user) if user else set()
            screens=db.scalars(select(Screen).order_by(Screen.sort_order)).all()
            for s in screens:
                rs=db.get(RoleScreenSetting,(user.role_id,s.screen_id)) if user else None
                visible[s.screen_code]=bool(is_super(db,user) or (rs and rs.show_screen and rs.can_view))
        db.close()
        return {'AR_WEEKDAYS':AR_WEEKDAYS,'AR_MONTHS':AR_MONTHS,'EVENT_AR':EVENT_AR,'MEETING_STATUS_AR':MEETING_STATUS_AR,'logged_in':bool(session.get('user_id')),'screen_visibility':visible,'permission_codes':perms,'is_super_admin': bool(user and user.role_id=='R001')}
