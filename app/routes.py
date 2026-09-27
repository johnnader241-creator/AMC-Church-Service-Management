from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, jsonify, current_app
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import joinedload
from .db import get_db
from .models import *
from .core.security import *
from .core.i18n import *
from .core.rules import *
import secrets, json, urllib.parse, hmac

web=Blueprint('web',__name__)

@web.app_template_global()
def arabic_weekday(code): return AR_WEEKDAYS.get(code,code)

@web.before_app_request
def app_request_guard():
    if request.endpoint in (None,'web.login','web.static') or request.path.startswith('/static/'):
        return
    if request.endpoint in {'web.login','web.health','web.api_health'}:
        return
    # CSRF protection for all state-changing browser requests.
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        expected=session.get('_csrf_token')
        supplied=request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            abort(400, description='Invalid CSRF token')
    if 'user_id' not in session: return redirect(url_for('web.login',next=request.path))

@web.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        db=get_db(); user=db.scalar(select(User).where(User.username==request.form.get('username','').strip(),User.is_active==True))
        ok=bool(user and verify_password(user,request.form.get('password','')))
        if ok:
            session.clear(); session['user_id']=user.user_id; session['_csrf_token']=secrets.token_urlsafe(32); session.permanent=True
            user.last_login_at=now(); audit(db,user,'LOGIN_SUCCESS','Users',user.user_id,new={'username':user.username}); db.commit(); db.close()
            return redirect(request.args.get('next') or url_for('web.dashboard'))
        db.close(); flash('بيانات الدخول غير صحيحة.','error')
    return render_template('login.html',user=None,title='تسجيل الدخول')

@web.post('/logout')
def logout():
    db=get_db(); user=current_user(db)
    if user: audit(db,user,'LOGOUT','Users',user.user_id,new={'username':user.username}); db.commit()
    db.close(); session.clear(); return redirect(url_for('web.login'))

@web.route('/health')
def health(): return jsonify(ok=True)

@web.route('/')
def dashboard():
    db=get_db(); user=current_user(db)
    services=list(db.scalars(select(Service).where(Service.status=='ACTIVE').order_by(Service.day_of_week,Service.service_name)))
    allowed=accessible_services(db,user); services=[s for s in services if s.service_id in allowed]
    year=get_open_year(db); meetings=[]
    if year: meetings=list(db.scalars(select(Meeting).where(Meeting.service_year_id==year.service_year_id).order_by(Meeting.meeting_date.desc()).limit(20)))
    counts={
      'servants':db.scalar(select(func.count()).select_from(Servant).where(Servant.status=='ACTIVE')) or 0,
      'services':len(services),'meetings':len(meetings),
      'events':db.scalar(select(func.count()).select_from(Event)) or 0,
      'openings':db.scalar(select(func.count()).select_from(Opening)) or 0,
    }
    activity=list(db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(8)))
    db.close(); return render_template('dashboard.html',user=user,services=services,meetings=meetings,counts=counts,activity=activity,year=year)

@web.route('/servants')
@require_screen('SERVANTS','VIEW')
def servants():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user)
    servants=list(db.scalars(select(Servant).where(Servant.status=='ACTIVE').order_by(Servant.name)))
    assignments=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id.in_(allowed)).order_by(ServiceAssignment.start_date.desc()))) if allowed else []
    services={s.service_id:s for s in db.scalars(select(Service).where(Service.service_id.in_(allowed))).all()}
    db.close(); return render_template('servants.html',user=user,servants=servants,assignments=assignments,services=services)

@web.route('/control')
@require_screen('CONTROL_CENTER','VIEW')
def control():
    db=get_db(); user=current_user(db)
    if not is_super(db,user): abort(403)
    roles=list(db.scalars(select(Role).order_by(Role.display_name))); perms=list(db.scalars(select(Permission).order_by(Permission.permission_code))); screens=list(db.scalars(select(Screen).order_by(Screen.sort_order)))
    users=list(db.scalars(select(User).order_by(User.username))); services=list(db.scalars(select(Service).order_by(Service.service_name))); years=list(db.scalars(select(ServiceYear).order_by(ServiceYear.start_date.desc())))
    scopes=list(db.scalars(select(UserServiceScope).order_by(UserServiceScope.user_id)))
    rs=list(db.scalars(select(RoleScreenSetting))); rp=list(db.scalars(select(RolePermission))); ov=list(db.scalars(select(UserPermissionOverride)))
    selected_role_id=request.args.get('role_id') or (roles[0].role_id if roles else None)
    selected_role=db.get(Role,selected_role_id) if selected_role_id else None
    selected_perm_ids={x.permission_id for x in rp if x.role_id==selected_role_id}
    db.close(); return render_template('control.html',user=user,roles=roles,perms=perms,screens=screens,users=users,services=services,years=years,scopes=scopes,rs=rs,rp=rp,ov=ov,selected_role=selected_role,selected_role_id=selected_role_id,selected_perm_ids=selected_perm_ids)

@web.post('/control/services/create')
def create_service():
    db=get_db(); user=current_user(db)
    if not is_super(db,user): abort(403)
    name=request.form.get('service_name','').strip(); stage=request.form.get('stage','').strip(); day=request.form.get('day_of_week','').strip().upper()
    if db.scalar(select(Service).where(Service.service_name==name)): flash('اسم الخدمة مستخدم بالفعل.','error')
    elif day not in ('THURSDAY','FRIDAY'): flash('اليوم يجب أن يكون الخميس أو الجمعة.','error')
    else:
        s=Service(service_id=next_id(db,Service,'service_id','SV',3),service_name=name,stage=stage,day_of_week=day,status='ACTIVE',opening_enabled=True); db.add(s); audit(db,user,'CREATE','Services',s.service_id,new={'service_name':name,'stage':stage,'day_of_week':day}); db.commit(); flash('تم إنشاء الخدمة.','ok')
    db.close(); return redirect(url_for('web.control'))

@web.post('/control/servants/create')
def create_servant():
    db=get_db(); user=current_user(db)
    if not user or not (is_super(db,user) or has_perm(db,user,'CREATE_SERVANTS')): abort(403)
    name=request.form.get('name','').strip()
    service_id=request.form.get('service_id','').strip() or None
    next_url=request.form.get('next') or url_for('web.control')
    if not name:
        flash('اسم الخادم مطلوب.','error')
    else:
        service=db.get(Service,service_id) if service_id else None
        year=get_open_year(db)
        start_raw=request.form.get('start_date','').strip(); end_raw=request.form.get('end_date','').strip()
        try:
            start=datetime.strptime(start_raw,'%Y-%m-%d').date() if start_raw else (year.start_date if year else None)
            end=datetime.strptime(end_raw,'%Y-%m-%d').date() if end_raw else (year.end_date if year else None)
        except ValueError:
            start=end=None
        if service_id and (not service or service.status!='ACTIVE'):
            flash('الخدمة غير موجودة أو غير نشطة.','error')
        elif service_id and not (is_super(db,user) or scope_allows(db,user,service_id)):
            flash('ليس لديك نطاق على هذه الخدمة.','error')
        elif service_id and (not year or not start or not end or not in_service_year(year,start,end)):
            flash('توزيع الخادم يجب أن يكون داخل سنة خدمة مفتوحة.','error')
        elif service_id and not start <= end:
            flash('تاريخ البداية يجب أن يسبق تاريخ النهاية.','error')
        else:
            s=Servant(servant_id=next_id(db,Servant,'servant_id','S',3),name=name,status='ACTIVE'); db.add(s); db.flush()
            audit(db,user,'CREATE','Servants',s.servant_id,new={'name':name,'status':'ACTIVE'})
            if service_id:
                a=ServiceAssignment(assignment_id=next_id(db,ServiceAssignment,'assignment_id','ASN',6),servant_id=s.servant_id,service_id=service_id,service_year_id=year.service_year_id,start_date=start,end_date=end,reason='التعيين عند إنشاء الخادم',created_by=user.user_id,updated_by=user.user_id)
                if overlapping_assignment(db,s.servant_id,service_id,start,end) or servant_day_conflict(db,s.servant_id,service.day_of_week,start,end):
                    db.rollback(); flash('لا يمكن تعيين الخادم: يوجد تعارض في نفس الخدمة/اليوم.','error'); db.close(); return redirect(next_url)
                db.add(a); audit(db,user,'CREATE','Service_Assignments',a.assignment_id,new={'servant_id':s.servant_id,'service_id':service_id,'start':str(start),'end':str(end)})
            db.commit(); flash('تم إضافة الخادم'+(' وتعيينه للخدمة.' if service_id else '.'),'ok')
    db.close(); return redirect(next_url)

@web.post('/control/service-years/create')
def create_year():
    db=get_db(); user=current_user(db)
    if not is_super(db,user): abort(403)
    start=datetime.strptime(request.form['start_date'],'%Y-%m-%d').date(); end=datetime.strptime(request.form['end_date'],'%Y-%m-%d').date()
    if start>=end: flash('تواريخ السنة غير صحيحة.','error'); db.close(); return redirect(url_for('web.control'))
    last=db.scalar(select(ServiceYear).where(ServiceYear.is_archived==False).order_by(ServiceYear.end_date.desc()))
    if last and start != last.end_date + timedelta(days=1): flash('السنة الجديدة يجب أن تبدأ بعد نهاية آخر سنة تشغيلية مباشرة.','error'); db.close(); return redirect(url_for('web.control'))
    if db.scalar(select(ServiceYear).where(ServiceYear.status=='OPEN',ServiceYear.is_archived==False)): flash('هناك Service Year مفتوحة بالفعل.','error'); db.close(); return redirect(url_for('web.control'))
    syname=f'{start.year}-{end.year}'; y=ServiceYear(service_year_id=f'SY{start.year}-{end.year}',year_name=syname,start_date=start,end_date=end,status='OPEN',created_by=user.user_id,updated_by=user.user_id); db.add(y); db.flush()
    services=list(db.scalars(select(Service).where(Service.status=='ACTIVE')))
    batch=f'GEN-{y.service_year_id}-{secrets.token_hex(4)}'
    for s in services:
        for d in fridays(start,end,s.day_of_week):
            mt=Meeting(meeting_id=next_id(db,Meeting,'meeting_id','MTG',6),service_year_id=y.service_year_id,service_id=s.service_id,meeting_date=d,day_of_week=s.day_of_week,status='SCHEDULED',generation_batch_id=batch,updated_by=user.user_id); db.add(mt)
    audit(db,user,'CREATE','Service_Years',y.service_year_id,new={'year_name':y.year_name,'start_date':str(start),'end_date':str(end)})
    db.commit(); db.close(); flash('تم إنشاء السنة وتوليد الاجتماعات للخدمات النشطة.','ok'); return redirect(url_for('web.control'))

@web.post('/services/<service_id>/assign')
def assign_servant(service_id):
    db=get_db(); user=current_user(db); service=db.get(Service,service_id)
    if not service or not scope_allows(db,user,service_id) or not has_perm(db,user,'EDIT_SERVANTS'): abort(403)
    sid=request.form.get('servant_id'); servant=db.get(Servant,sid); year=get_open_year(db)
    try:
        start=datetime.strptime(request.form['start_date'],'%Y-%m-%d').date(); end=datetime.strptime(request.form['end_date'],'%Y-%m-%d').date()
    except: flash('التواريخ غير صحيحة.','error'); db.close(); return redirect(url_for('web.servants'))
    if not servant or servant.status!='ACTIVE': flash('الخادم غير نشط.','error')
    elif not year or not in_service_year(year,start,end): flash('الـAssignment يجب أن تكون داخل سنة خدمة مفتوحة.','error')
    elif overlapping_assignment(db,sid,service_id,start,end): flash('يوجد تعارض داخل نفس الخدمة.','error')
    elif servant_day_conflict(db,sid,service.day_of_week,start,end): flash('الخادم لديه خدمة أخرى في نفس اليوم خلال هذه الفترة.','error')
    else:
        a=ServiceAssignment(assignment_id=next_id(db,ServiceAssignment,'assignment_id','ASN',6),servant_id=sid,service_id=service_id,service_year_id=year.service_year_id,start_date=start,end_date=end,reason=request.form.get('reason') or None,created_by=user.user_id,updated_by=user.user_id); db.add(a); audit(db,user,'CREATE','Service_Assignments',a.assignment_id,new={'servant_id':sid,'service_id':service_id}); db.commit(); flash('تم توزيع الخادم.','ok')
    db.close(); return redirect(url_for('web.servants'))

@web.route('/evaluations')
@require_screen('EVALUATIONS','VIEW')
def evaluations():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); year=get_open_year(db)
    rows=list(db.scalars(select(Meeting).where(Meeting.service_id.in_(allowed),Meeting.service_year_id==year.service_year_id if year else False).order_by(Meeting.meeting_date.desc()).limit(100))) if allowed and year else []
    svc={s.service_id:s for s in db.scalars(select(Service).where(Service.service_id.in_(allowed))).all()}; db.close(); return render_template('evaluations.html',user=user,meetings=rows,services=svc)

@web.route('/meetings/<meeting_id>')
@require_screen('EVALUATIONS','VIEW')
def meeting_detail(meeting_id):
    db=get_db(); user=current_user(db); m=db.get(Meeting,meeting_id)
    if not m or not scope_allows(db,user,m.service_id,m.meeting_date): abort(404)
    if m.status!='COMPLETED': flash('التقييم لا يفتح إلا بعد تحويل الاجتماع إلى Completed.','info')
    # draft records for active assignment members on date
    assigned=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id==m.service_id,ServiceAssignment.start_date<=m.meeting_date,ServiceAssignment.end_date>=m.meeting_date)))
    for a in assigned:
        if not db.scalar(select(Evaluation).where(Evaluation.meeting_id==m.meeting_id,Evaluation.servant_id==a.servant_id)):
            db.add(Evaluation(evaluation_id=next_id(db,Evaluation,'evaluation_id','EVAL',8),meeting_id=m.meeting_id,servant_id=a.servant_id,evaluation_status='NOT_ENTERED'))
    db.commit()
    evals=list(db.scalars(select(Evaluation).where(Evaluation.meeting_id==m.meeting_id).order_by(Evaluation.servant_id)))
    names={s.servant_id:s.name for s in db.scalars(select(Servant).where(Servant.servant_id.in_([a.servant_id for a in assigned]))).all()}
    svc=db.get(Service,m.service_id)
    db.close(); return render_template('meeting.html',user=user,meeting=m,service=svc,evals=evals,names=names)

@web.post('/meetings/<meeting_id>/complete')
def complete_meeting(meeting_id):
    db=get_db(); user=current_user(db); m=db.get(Meeting,meeting_id)
    if not m or not has_perm(db,user,'EDIT_EVALUATIONS') or not scope_allows(db,user,m.service_id): abort(403)
    if m.status=='SCHEDULED': m.status='COMPLETED'; m.completed_at=now(); m.completed_by=user.user_id; m.updated_by=user.user_id; audit(db,user,'UPDATE','Meetings',m.meeting_id,old={'status':'SCHEDULED'},new={'status':'COMPLETED'}); db.commit(); flash('تم إغلاق الاجتماع كـCompleted.','ok')
    db.close(); return redirect(url_for('web.meeting_detail',meeting_id=meeting_id))

@web.post('/meetings/<meeting_id>/save')
def save_meeting_evaluations(meeting_id):
    db=get_db(); user=current_user(db); m=db.get(Meeting,meeting_id)
    if not m or m.status!='COMPLETED' or not has_perm(db,user,'EDIT_EVALUATIONS') or not scope_allows(db,user,m.service_id): abort(403)
    evs=list(db.scalars(select(Evaluation).where(Evaluation.meeting_id==meeting_id)))
    svc=db.get(Service,m.service_id); oldvals={};
    for e in evs:
        oldvals[e.evaluation_id]=dict(preparation=e.preparation,service_attendance=e.service_attendance,family_meeting=e.family_meeting,mass_attendance=e.mass_attendance,evaluation_status=e.evaluation_status)
        def val(name):
            raw=request.form.get(f'{e.servant_id}_{name}')
            return True if raw=='1' else False
        e.preparation=val('preparation'); e.service_attendance=val('service_attendance'); e.family_meeting=val('family_meeting')
        e.mass_attendance=val('mass_attendance') if svc.day_of_week=='FRIDAY' else None
        e.preparation_status=e.service_attendance_status=e.family_meeting_status='EVALUATED'; e.mass_attendance_status='EVALUATED' if svc.day_of_week=='FRIDAY' else None
        e.evaluation_status='EVALUATED'; e.entered_by=user.user_id; e.entered_at=e.entered_at or now(); e.updated_by=user.user_id; e.updated_at=now()
        audit(db,user,'UPDATE','Servant_Meeting_Evaluations',e.evaluation_id,old=oldvals[e.evaluation_id],new={'preparation':e.preparation,'service_attendance':e.service_attendance,'family_meeting':e.family_meeting,'mass_attendance':e.mass_attendance,'evaluation_status':'EVALUATED'})
    db.commit(); db.close(); flash('تم حفظ التقييمات.','ok'); return redirect(url_for('web.meeting_detail',meeting_id=meeting_id))

@web.route('/events')
@require_screen('EVALUATIONS','VIEW')
def events():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); rows=list(db.scalars(select(Event).where(Event.service_id.in_(allowed)).order_by(Event.event_date.desc()))) if allowed else []
    svcs={s.service_id:s for s in db.scalars(select(Service).where(Service.service_id.in_(allowed))).all()}; db.close(); return render_template('events.html',user=user,events=rows,services=svcs)

@web.post('/events/create')
def create_event():
    db=get_db(); user=current_user(db); sid=request.form.get('service_id');
    if not sid or not scope_allows(db,user,sid) or not has_perm(db,user,'EDIT_EVENTS'): abort(403)
    svc=db.get(Service,sid); year=get_open_year(db)
    ed=datetime.strptime(request.form['event_date'],'%Y-%m-%d').date(); et=request.form['event_type']; name=request.form.get('event_name','').strip()
    if not year or not (year.start_date<=ed<=year.end_date): flash('تاريخ الحدث خارج سنة الخدمة.','error')
    elif db.scalar(select(Event).where(Event.service_id==sid,Event.event_date==ed)): flash('يوجد Event بالفعل في هذا التاريخ للخدمة.','error')
    else:
        ev=Event(event_id=next_id(db,Event,'event_id','EVT',6),service_id=sid,service_year_id=year.service_year_id,event_name=name,event_date=ed,event_type=et,affects_meeting=False,created_by=user.user_id,updated_by=user.user_id); db.add(ev); db.flush()
        # auto-build participant list from assignments on event date
        assigns=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id==sid,ServiceAssignment.start_date<=ed,ServiceAssignment.end_date>=ed)))
        if not assigns:
            db.delete(ev); db.commit(); flash('لا يمكن إنشاء Event بدون مشارك واحد على الأقل.','error'); db.close(); return redirect(url_for('web.events'))
        for a in assigns:
            db.add(Participant(participant_id=next_id(db,Participant,'participant_id','PAR',6),event_id=ev.event_id,servant_id=a.servant_id,participation_status='PARTICIPATED',created_by=user.user_id,updated_by=user.user_id))
        audit(db,user,'CREATE','Events',ev.event_id,new={'service_id':sid,'event_date':str(ed),'event_type':et}); db.commit(); flash('تم إنشاء الحدث وتكوين قائمة المشاركين.','ok')
    db.close(); return redirect(url_for('web.events'))

@web.route('/events/<event_id>')
@require_screen('EVALUATIONS','VIEW')
def event_detail(event_id):
    db=get_db(); user=current_user(db); ev=db.get(Event,event_id)
    if not ev or not scope_allows(db,user,ev.service_id,ev.event_date): abort(404)
    parts=list(db.scalars(select(Participant).where(Participant.event_id==event_id)))
    names={s.servant_id:s.name for s in db.scalars(select(Servant).where(Servant.servant_id.in_([p.servant_id for p in parts]))).all()}
    meetings=list(db.scalars(select(Meeting).where(Meeting.service_id==ev.service_id,Meeting.service_year_id==ev.service_year_id,Meeting.status=='COMPLETED').order_by(Meeting.meeting_date.desc())))
    db.close(); return render_template('event_detail.html',user=user,event=ev,participants=parts,names=names,meetings=meetings)

@web.post('/events/<event_id>/participant/<servant_id>/toggle')
def toggle_participant(event_id,servant_id):
    db=get_db(); user=current_user(db); ev=db.get(Event,event_id)
    if not ev or not has_perm(db,user,'EDIT_EVENTS') or not scope_allows(db,user,ev.service_id,ev.event_date): abort(403)
    p=db.scalar(select(Participant).where(Participant.event_id==event_id,Participant.servant_id==servant_id))
    if p: p.participation_status='NOT_PARTICIPATED' if p.participation_status=='PARTICIPATED' else 'PARTICIPATED'; p.updated_by=user.user_id; audit(db,user,'UPDATE','Meeting_Participants',p.participant_id,new={'participation_status':p.participation_status})
    db.commit(); db.close(); return redirect(url_for('web.event_detail',event_id=event_id))

@web.post('/events/<event_id>/apply-evaluation')
def apply_event_evaluation(event_id):
    db=get_db(); user=current_user(db); ev=db.get(Event,event_id)
    if not ev or not has_perm(db,user,'EDIT_EVALUATIONS') or not ev.affected_meeting_id: abort(403)
    m=db.get(Meeting,ev.affected_meeting_id); svc=db.get(Service,m.service_id); parts=list(db.scalars(select(Participant).where(Participant.event_id==event_id)))
    for p in parts:
        e=db.scalar(select(Evaluation).where(Evaluation.meeting_id==m.meeting_id,Evaluation.servant_id==p.servant_id))
        if not e: continue
        e.event_id=ev.event_id
        if ev.event_type in ('CONFERENCE','TRIP') and p.participation_status=='PARTICIPATED':
            e.preparation=e.service_attendance=e.family_meeting=True; e.mass_attendance=True if svc.day_of_week=='FRIDAY' else None; e.preparation_status=e.service_attendance_status=e.family_meeting_status='SERVICE_EVENT_FULL'; e.mass_attendance_status='SERVICE_EVENT_FULL' if svc.day_of_week=='FRIDAY' else None; e.evaluation_status='SERVICE_EVENT_FULL'
        elif ev.event_type in ('PROJECT','SPORTS_DAY') and p.participation_status=='PARTICIPATED': e.evaluation_status='SERVICE_EVENT_REVIEW'
        e.updated_by=user.user_id; e.updated_at=now()
    audit(db,user,'UPDATE','Events',ev.event_id,new={'applied_to_meeting':m.meeting_id}); db.commit(); db.close(); flash('تم دفع تقييم الحدث إلى نظام التقييم.','ok'); return redirect(url_for('web.event_detail',event_id=event_id))

@web.route('/excuses')
@require_screen('EVALUATIONS','VIEW')
def excuses():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); year=get_open_year(db)
    rows=list(db.scalars(select(Excuse).join(Meeting).where(Meeting.service_id.in_(allowed)).order_by(Excuse.created_at.desc()))) if allowed else []
    services=list(db.scalars(select(Service).where(Service.service_id.in_(allowed),Service.status=='ACTIVE').order_by(Service.day_of_week,Service.service_name))) if allowed else []
    meetings=list(db.scalars(select(Meeting).where(Meeting.service_id.in_(allowed),Meeting.service_year_id==year.service_year_id).order_by(Meeting.meeting_date.desc()))) if allowed and year else []
    servants=list(db.scalars(select(Servant).where(Servant.status=='ACTIVE').order_by(Servant.name)))
    assignments=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id.in_(allowed)))) if allowed else []
    names={s.servant_id:s.name for s in servants}; service_names={s.service_id:s.service_name for s in services}; meeting_map={m.meeting_id:m for m in meetings}; db.close(); return render_template('excuses.html',user=user,excuses=rows,services=services,meetings=meetings,servants=servants,assignments=assignments,names=names,service_names=service_names,meeting_map=meeting_map)

@web.post('/excuses/create')
def create_excuse():
    db=get_db(); user=current_user(db); meeting=db.get(Meeting,request.form.get('meeting_id')); sid=request.form.get('servant_id')
    if not meeting or not has_perm(db,user,'CREATE_EXCUSES') or not scope_allows(db,user,meeting.service_id,meeting.meeting_date): abort(403)
    ass=db.scalar(select(ServiceAssignment).where(ServiceAssignment.service_id==meeting.service_id,ServiceAssignment.servant_id==sid,ServiceAssignment.start_date<=meeting.meeting_date,ServiceAssignment.end_date>=meeting.meeting_date))
    if not ass: flash('الخادم ليس عضوًا في الخدمة في تاريخ الاجتماع.','error')
    else:
        ev=db.scalar(select(Evaluation).where(Evaluation.meeting_id==meeting.meeting_id,Evaluation.servant_id==sid)); snap=None
        if ev: snap={'evaluation_id':ev.evaluation_id,'preparation':ev.preparation,'preparation_status':ev.preparation_status,'service_attendance':ev.service_attendance,'service_attendance_status':ev.service_attendance_status,'family_meeting':ev.family_meeting,'family_meeting_status':ev.family_meeting_status,'mass_attendance':ev.mass_attendance,'mass_attendance_status':ev.mass_attendance_status,'evaluation_status':ev.evaluation_status}
        ex=Excuse(excuse_id=next_id(db,Excuse,'excuse_id','EXC',6),servant_id=sid,meeting_id=meeting.meeting_id,evaluation_id=ev.evaluation_id if ev else None,reason=request.form.get('reason','').strip(),status='PENDING',submitted_by=user.user_id,evaluation_snapshot=snap); db.add(ex); audit(db,user,'CREATE','Excuses',ex.excuse_id,new={'servant_id':sid,'meeting_id':meeting.meeting_id}); db.commit(); flash('تم تسجيل الاعتذار للمراجعة.','ok')
    db.close(); return redirect(url_for('web.excuses'))

@web.post('/excuses/<excuse_id>/review')
def review_excuse(excuse_id):
    db=get_db(); user=current_user(db); ex=db.get(Excuse,excuse_id)
    if not ex or not is_super(db,user) or not has_perm(db,user,'REVIEW_EXCUSES'): abort(403)
    decision=request.form.get('decision');
    if decision not in ('APPROVED','REJECTED'): abort(400)
    if ex.status!='PENDING': flash('الاعتذار تمت مراجعته بالفعل.','info'); db.close(); return redirect(url_for('web.excuses'))
    ex.status=decision; ex.reviewed_by=user.user_id; ex.reviewed_at=now()
    if decision=='APPROVED':
        ex.approved_at=now(); ex.approval_note=request.form.get('approval_note') or None
        if ex.evaluation_id:
            ev=db.get(Evaluation,ex.evaluation_id)
            if ev: ev.evaluation_status='ARCHIVED'; ev.archived_at=now(); ev.archived_by=user.user_id; ev.archive_reason='APPROVED_EXCUSE'; ex.evaluation_snapshot=ex.evaluation_snapshot or {}
    else:
        ex.rejection_reason=request.form.get('rejection_reason','').strip()
        if ex.evaluation_snapshot and ex.evaluation_id:
            ev=db.get(Evaluation,ex.evaluation_id)
            if ev:
                for k,v in ex.evaluation_snapshot.items():
                    if k!='evaluation_id' and hasattr(ev,k): setattr(ev,k,v)
                ev.updated_by=user.user_id; ev.updated_at=now()
        else:
            # create zero evaluation if none existed
            meeting=db.get(Meeting,ex.meeting_id); svc=db.get(Service,meeting.service_id); ev=Evaluation(evaluation_id=ex.evaluation_id or next_id(db,Evaluation,'evaluation_id','EVAL',8),meeting_id=ex.meeting_id,servant_id=ex.servant_id,evaluation_status='EVALUATED',preparation=False,service_attendance=False,family_meeting=False,mass_attendance=False if svc.day_of_week=='FRIDAY' else None); db.add(ev); ex.evaluation_id=ev.evaluation_id
    audit(db,user,'UPDATE','Excuses',ex.excuse_id,new={'status':decision}); db.commit(); db.close(); flash('تمت مراجعة الاعتذار.','ok'); return redirect(url_for('web.excuses'))

@web.post('/evaluations/<evaluation_id>/exclude')
def exclude_evaluation(evaluation_id):
    db=get_db(); user=current_user(db); e=db.get(Evaluation,evaluation_id)
    allowed_reasons={'خطأ إدخال','تكرار','فقدان الورقة','سبب إداري','أخرى'}
    if not e or not is_super(db,user) or not has_perm(db,user,'EXCLUDE_EVALUATIONS') or e.evaluation_status!='NOT_ENTERED': abort(403)
    reason=request.form.get('reason','').strip(); note=request.form.get('note','').strip() or None
    if reason not in allowed_reasons: flash('سبب الاستبعاد غير صالح.','error')
    else:
        e.evaluation_status='EXCLUDED'; e.excluded_reason=reason; e.excluded_note=note; e.excluded_at=now(); e.excluded_by=user.user_id; audit(db,user,'EXCLUDE','Servant_Meeting_Evaluations',e.evaluation_id,new={'status':'EXCLUDED','reason':reason,'note':note}); db.commit(); flash('تم استبعاد التقييم من الحساب.','ok')
    db.close(); return redirect(url_for('web.meeting_detail',meeting_id=e.meeting_id))

@web.route('/results')
@require_screen('RESULTS','VIEW')
def results():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); year=get_open_year(db)
    if not year or not allowed: db.close(); return render_template('results.html',user=user,rows=[],service_rows=[],year=year)
    meetings={m.meeting_id:m for m in db.scalars(select(Meeting).where(Meeting.service_year_id==year.service_year_id,Meeting.service_id.in_(allowed),Meeting.status=='COMPLETED')).all()}
    evals=list(db.scalars(select(Evaluation).where(Evaluation.meeting_id.in_(list(meetings.keys())),Evaluation.evaluation_status.not_in(['ARCHIVED','EXCLUDED'])))) if meetings else []
    servant_objs=list(db.scalars(select(Servant).where(Servant.status=='ACTIVE').order_by(Servant.name)))
    rows=[]
    months=[11,12,1,2,3,4,5,6,7]
    fields=[('preparation','التحضير'),('service_attendance','حضور الخدمة'),('family_meeting','اجتماع الأسرة'),('mass_attendance','حضور القداس')]
    for servant in servant_objs:
        sev=[e for e in evals if e.servant_id==servant.servant_id]
        monthly={}; annual_crit={}
        for mnum in months:
            mes=[e for e in sev if meetings[e.meeting_id].meeting_date.month==mnum]
            if not mes: continue
            criterion={}
            for field,label in fields:
                vals=[getattr(e,field) for e in mes if getattr(e,field) is not None]
                criterion[field]=round(sum(bool(v) for v in vals)*100/len(vals),1) if vals else None
            available=[v for v in criterion.values() if v is not None]
            monthly[mnum]={'overall':round(sum(available)/len(available),1) if available else None,**criterion}
        for field,label in fields:
            vals=[monthly[m][field] for m in monthly if monthly[m].get(field) is not None]
            annual_crit[field]=round(sum(vals)/len(vals),1) if vals else None
        overall=[monthly[m]['overall'] for m in monthly if monthly[m].get('overall') is not None]
        rows.append({'servant':servant.name,'annual':round(sum(overall)/len(overall),1) if overall else None,'annual_criteria':annual_crit,'monthly':monthly})
    # service-level annual result, average of servant annual scores
    service_rows=[]
    services=list(db.scalars(select(Service).where(Service.service_id.in_(allowed),Service.status=='ACTIVE').order_by(Service.service_name)))
    for svc in services:
        sr=[r for r in rows if any(e.servant_id and meetings[e.meeting_id].service_id==svc.service_id for e in evals if e.servant_id and e.meeting_id in meetings and r['servant']==next((x.name for x in servant_objs if x.servant_id==e.servant_id),''))]
        # Easier robust calculation: map servant names participating in this service.
        names={s.name for s in servant_objs if any(e.servant_id==s.servant_id and meetings[e.meeting_id].service_id==svc.service_id for e in evals if e.meeting_id in meetings)}
        sr=[r for r in rows if r['servant'] in names and r['annual'] is not None]
        service_rows.append({'service':svc.service_name,'annual':round(sum(r['annual'] for r in sr)/len(sr),1) if sr else None})
    db.close(); return render_template('results.html',user=user,rows=rows,service_rows=service_rows,year=year)

@web.route('/openings')
@require_screen('OPENINGS','VIEW')
def openings():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); year=get_open_year(db); services=list(db.scalars(select(Service).where(Service.service_id.in_(allowed),Service.status=='ACTIVE',Service.opening_enabled==True).order_by(Service.day_of_week,Service.service_name))) if allowed else []
    openings=list(db.scalars(select(Opening).where(Opening.service_id.in_(allowed),Opening.service_year_id==year.service_year_id if year else False).order_by(Opening.friday_date))) if allowed and year else []
    db.close(); return render_template('openings.html',user=user,services=services,openings=openings,year=year)

@web.post('/openings/create')
def create_opening():
    db=get_db(); user=current_user(db); sid=request.form.get('service_id');
    if not sid or not scope_allows(db,user,sid) or not has_perm(db,user,'EDIT_OPENINGS'): abort(403)
    year=db.get(ServiceYear,request.form.get('service_year_id')); svc=db.get(Service,sid); d=datetime.strptime(request.form['friday_date'],'%Y-%m-%d').date();
    if not svc or not svc.opening_enabled: flash('الافتتاحيات غير مفعلة لهذه الخدمة.','error')
    elif d.weekday()!=4: flash('التاريخ يجب أن يكون جمعة.','error')
    elif not year or not (year.start_date<=d<=year.end_date): flash('التاريخ خارج سنة الخدمة.','error')
    elif not is_url(request.form.get('link','')): flash('الرابط يجب أن يكون URL صالحًا.','error')
    else:
        period=int(request.form['period_no']); month=d.month
        if db.scalar(select(Opening).where(Opening.service_id==sid,Opening.service_year_id==year.service_year_id,Opening.friday_date==d)): flash('يوجد Opening بالفعل لنفس الخدمة والتاريخ.','error')
        else:
            op=Opening(opening_id=next_id(db,Opening,'opening_id','OPN',6),service_id=sid,service_year_id=year.service_year_id,period_no=period,month=month,friday_date=d,link=request.form['link'],created_by=user.user_id,updated_by=user.user_id); db.add(op); audit(db,user,'CREATE','Openings',op.opening_id,new={'service_id':sid,'friday_date':str(d),'link':op.link}); db.commit(); flash('تم حفظ الافتتاحية.','ok')
    db.close(); return redirect(url_for('web.openings'))

@web.post('/openings/swap')
def swap_openings():
    db=get_db(); user=current_user(db); a=db.get(Opening,request.form.get('source_id')); b=db.get(Opening,request.form.get('target_id'))
    if not a or not b or a.service_id!=b.service_id or not has_perm(db,user,'MANAGE_OPENING_TRANSFERS') or not scope_allows(db,user,a.service_id): abort(403)
    a.link,b.link=b.link,a.link; a.period_no,b.period_no=b.period_no,a.period_no; a.month,b.month=b.month,a.month; db.commit(); audit(db,user,'OPENING_SWAP','Openings',a.opening_id,new={'swapped_with':b.opening_id}); audit(db,user,'OPENING_SWAP','Openings',b.opening_id,new={'swapped_with':a.opening_id}); db.commit(); flash('تم تبديل الافتتاحيتين.','ok'); db.close(); return redirect(url_for('web.openings'))

@web.route('/transfers')
@require_screen('SERVANTS','VIEW')
def transfers():
    db=get_db(); user=current_user(db); allowed=accessible_services(db,user); rows=list(db.scalars(select(ServiceTransfer).where(ServiceTransfer.from_service_id.in_(allowed)).order_by(ServiceTransfer.requested_at.desc()))) if allowed else []
    services=list(db.scalars(select(Service).where(Service.service_id.in_(allowed),Service.status=='ACTIVE').order_by(Service.day_of_week,Service.service_name))) if allowed else []
    servants=list(db.scalars(select(Servant).where(Servant.status=='ACTIVE').order_by(Servant.name)))
    assignments=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id.in_(allowed)))) if allowed else []
    db.close(); return render_template('transfers.html',user=user,transfers=rows,services=services,servants=servants,assignments=assignments)

@web.post('/transfers/create')
def create_transfer():
    db=get_db(); user=current_user(db); sid=request.form.get('servant_id'); frm=request.form.get('from_service_id'); to=request.form.get('to_service_id');
    if not has_perm(db,user,'CREATE_TRANSFERS') or not scope_allows(db,user,frm): abort(403)
    if not transfer_window_open(date.today()) and not is_super(db,user): flash('خارج نافذة النقل الحالية.','error')
    else:
        today=date.today(); effective=(today.replace(day=1)+timedelta(days=32)).replace(day=1)
        active=db.scalar(select(ServiceAssignment).where(ServiceAssignment.servant_id==sid,ServiceAssignment.service_id==frm,ServiceAssignment.start_date<=today,ServiceAssignment.end_date>=today))
        if not active: flash('لا توجد Assignment فعالة في الخدمة الحالية.','error')
        elif db.scalar(select(ServiceTransfer).where(ServiceTransfer.servant_id==sid,ServiceTransfer.status=='PENDING')): flash('يوجد طلب نقل مفتوح.','error')
        else:
            t=ServiceTransfer(transfer_id=next_id(db,ServiceTransfer,'transfer_id','TRF',6),servant_id=sid,from_service_id=frm,to_service_id=to,effective_date=effective,requested_by=user.user_id,status='PENDING'); db.add(t); audit(db,user,'CREATE','Service_Transfers',t.transfer_id,new={'servant_id':sid,'from_service_id':frm,'to_service_id':to,'effective_date':str(effective)}); db.commit(); flash('تم إنشاء طلب النقل.','ok')
    db.close(); return redirect(url_for('web.transfers'))

@web.post('/transfers/<transfer_id>/destination-approve')
def destination_approve(transfer_id):
    db=get_db(); user=current_user(db); t=db.get(ServiceTransfer,transfer_id)
    if not t or not has_perm(db,user,'APPROVE_DESTINATION_TRANSFER') or not scope_allows(db,user,t.to_service_id): abort(403)
    if t.status=='PENDING': t.status='DESTINATION_APPROVED'; t.destination_approved_by=user.user_id; t.destination_approved_at=now(); audit(db,user,'UPDATE','Service_Transfers',t.transfer_id,new={'status':t.status}); db.commit();
    db.close(); return redirect(url_for('web.transfers'))

@web.post('/transfers/<transfer_id>/super-approve')
def super_approve_transfer(transfer_id):
    db=get_db(); user=current_user(db); t=db.get(ServiceTransfer,transfer_id)
    if not t or not is_super(db,user): abort(403)
    if t.status in ('PENDING','DESTINATION_APPROVED'):
        t.status='SUPER_ADMIN_APPROVED'; t.super_admin_approved_by=user.user_id; t.super_admin_approved_at=now();
        active=db.scalar(select(ServiceAssignment).where(ServiceAssignment.servant_id==t.servant_id,ServiceAssignment.service_id==t.from_service_id,ServiceAssignment.start_date<=t.effective_date,ServiceAssignment.end_date>=t.effective_date))
        if active:
            active.end_date=t.effective_date-timedelta(days=1)
            target_year=db.scalar(select(ServiceYear).where(ServiceYear.status=='OPEN',ServiceYear.is_archived==False,ServiceYear.start_date<=t.effective_date,ServiceYear.end_date>=t.effective_date)) or db.get(ServiceYear,active.service_year_id); newa=ServiceAssignment(assignment_id=next_id(db,ServiceAssignment,'assignment_id','ASN',6),servant_id=t.servant_id,service_id=t.to_service_id,service_year_id=target_year.service_year_id,start_date=t.effective_date,end_date=target_year.end_date,reason='TRANSFER',created_by=user.user_id,updated_by=user.user_id); db.add(newa); t.status='COMPLETED'; t.completed_by=user.user_id; t.completed_at=now(); audit(db,user,'UPDATE','Service_Transfers',t.transfer_id,new={'status':'COMPLETED','effective_date':str(t.effective_date)})
        db.commit()
    db.close(); return redirect(url_for('web.transfers'))

@web.errorhandler(403)
def forbidden(e):
    db=get_db(); u=current_user(db); db.close(); return render_template('403.html',user=u),403

@web.errorhandler(404)
def not_found(e):
    db=get_db(); u=current_user(db); db.close(); return render_template('404.html',user=u),404

@web.route('/otp/<screen>')
def otp_prompt(screen):
    if 'user_id' not in session: return redirect(url_for('web.login'))
    db=get_db(); user=current_user(db)
    try:
        if not user or not screen_allowed(db,user,screen,'VIEW'):
            abort(403)
        code=issue_otp(db,user,screen)
        db.commit()
    finally:
        db.close()
    # OTP codes are intentionally never rendered in production. A real delivery
    # provider should be connected before enabling OTP-required screens online.
    demo_code=code if current_app.config.get('APP_ENV') != 'production' else None
    return render_template('otp.html',user=user,screen=screen,demo_code=demo_code,next=request.args.get('next','/'))

@web.post('/otp/<screen>/verify')
def otp_verify(screen):
    db=get_db(); user=current_user(db); value=request.form.get('otp','').strip(); q=select(OTPSession).where(OTPSession.user_id==user.user_id,OTPSession.screen_code==screen,OTPSession.status=='ISSUED').order_by(OTPSession.issued_at.desc()); row=db.scalar(q)
    ok=False
    if row:
        if now()>row.expires_at: row.status='EXPIRED'
        elif row.lock_until and now()<row.lock_until: ok=False
        elif value==row.otp_code:
            row.status='USED'; row.used_at=now(); ok=True
            data=dict(session.get('otp_ok',{})); data[screen]=True; session['otp_ok']=data
            audit(db,user,'OTP_USED','OTP_Sessions',row.otp_session_id,new={'screen':screen})
        else:
            row.attempt_count+=1; row.last_attempt_at=now()
            settings=db.get(SecuritySetting,1); maxa=settings.otp_max_attempts
            if row.attempt_count>=maxa:
                row.status='FAILED'; row.failed_at=now(); row.lock_until=now()+timedelta(seconds=settings.otp_lock_seconds)
            audit(db,user,'OTP_FAILED','OTP_Sessions',row.otp_session_id,new={'screen':screen,'attempt_count':row.attempt_count})
        db.commit()
    db.close()
    if ok: return redirect(request.form.get('next') or url_for('web.dashboard'))
    flash('رمز OTP غير صحيح أو منتهي.','error'); return redirect(url_for('web.otp_prompt',screen=screen,next=request.form.get('next','/')))

@web.route('/database')
def database_explorer():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    tables=[Servant,Service,ServiceYear,ServiceAssignment,ServiceTransfer,Meeting,Event,Participant,Evaluation,Excuse,Opening,FollowupRecord,User,Role,Permission,RolePermission,UserServiceScope,OTPSession,AuditLog,TrashRecord]
    data=[]
    for m in tables:
        pk=list(m.__table__.primary_key.columns)[0]
        count=db.scalar(select(func.count()).select_from(m)) or 0
        data.append({'name':m.__tablename__,'count':count,'pk':pk.name})
    db.close(); return render_template('database.html',user=user,data=data)

@web.route('/trash')
def trash():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    rows=list(db.scalars(select(TrashRecord).order_by(TrashRecord.deleted_at.desc()).limit(200))); db.close(); return render_template('trash.html',user=user,rows=rows)

@web.route('/api/health')
def api_health(): return jsonify(status='ok',app='church-service-system',time=now().isoformat())

from .excel.engine import detect as excel_detect, FILE_MAP as EXCEL_FILES, SHEET_MAP as EXCEL_SHEETS, PK_MAP as EXCEL_PKS

@web.route('/control/excel')
def excel_review():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user) or not has_perm(db,user,'REVIEW_EXCEL_CHANGES'): abort(403)
    excel_error=None
    try:
        changes=excel_detect(db,user)
    except Exception as exc:
        changes=[]
        excel_error=f'{type(exc).__name__}: {exc}'
        app_logger = current_app.logger
        app_logger.exception('Excel review failed')
    finally:
        db.close()
    return render_template('excel.html',user=user,changes=changes,excel_error=excel_error)

@web.route('/control/users/reset',methods=['POST'])
def reset_user_password():
    db=get_db(); user=current_user(db); target=db.get(User,request.form.get('user_id'))
    if not user or not is_super(db,user) or not has_perm(db,user,'RESET_USER_PASSWORD') or not target: abort(403)
    target.password_hash=hash_password(request.form.get('password',''))
    audit(db,user,'RESET_PASSWORD','Users',target.user_id,new={'username':target.username}); db.commit(); db.close(); flash('تم تغيير كلمة المرور.','ok'); return redirect(url_for('web.control'))

@web.route('/services/<service_id>')
@require_screen('SERVANTS','VIEW')
def service_page(service_id):
    db=get_db(); user=current_user(db); svc=db.get(Service,service_id)
    if not svc or not scope_allows(db,user,service_id): abort(404)
    today=date.today(); members=list(db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_id==service_id,ServiceAssignment.start_date<=today,ServiceAssignment.end_date>=today)))
    servants={s.servant_id:s for s in db.scalars(select(Servant).where(Servant.servant_id.in_([m.servant_id for m in members]))).all()}
    all_servants=list(db.scalars(select(Servant).where(Servant.status=='ACTIVE').order_by(Servant.name)))
    db.close(); return render_template('service.html',user=user,service=svc,members=members,servants=servants,all_servants=all_servants,today=today)


@web.post('/control/screen-setting')
def update_screen_setting():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    role_id=request.form['role_id']; screen_id=request.form['screen_id']
    x=db.get(RoleScreenSetting,(role_id,screen_id))
    if not x: x=RoleScreenSetting(role_id=role_id,screen_id=screen_id); db.add(x)
    x.show_screen=request.form.get('show_screen')=='1'; x.can_view=request.form.get('can_view')=='1'; x.can_edit=request.form.get('can_edit')=='1'; x.otp_required=request.form.get('otp_required')=='1'
    if x.can_edit: x.can_view=True
    if x.otp_required: x.can_view=True
    x.revision_no=(x.revision_no or 0)+1; x.updated_by=user.user_id
    audit(db,user,'UPDATE','Role_Screen_Settings',f'{role_id}:{screen_id}',new={'show':x.show_screen,'view':x.can_view,'edit':x.can_edit,'otp':x.otp_required,'revision_no':x.revision_no}); db.commit(); db.close(); flash('تم تحديث إعدادات الشاشة.','ok'); return redirect(url_for('web.control'))

@web.post('/control/role/update')
def update_role():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    role_id=request.form['role_id']; display_name=request.form.get('display_name','').strip()
    role=db.get(Role,role_id)
    if not role or not display_name:
        flash('المسمى العام مطلوب.','error'); db.close(); return redirect(url_for('web.control',role_id=role_id))
    old=role.display_name; role.display_name=display_name; role.revision_no=(role.revision_no or 0)+1
    audit(db,user,'UPDATE','Roles',role_id,old={'display_name':old},new={'display_name':display_name,'revision_no':role.revision_no}); db.commit(); db.close(); flash('تم تحديث المسمى العام للدور.','ok'); return redirect(url_for('web.control',role_id=role_id))

@web.post('/control/role-permissions/bulk')
def update_role_permissions_bulk():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    role_id=request.form['role_id']; role=db.get(Role,role_id)
    if not role: abort(404)
    chosen=set(request.form.getlist('permission_id'))
    valid={p.permission_id for p in db.scalars(select(Permission))}
    chosen &= valid
    existing=list(db.scalars(select(RolePermission).where(RolePermission.role_id==role_id)))
    existing_map={x.permission_id:x for x in existing}
    for pid,row in existing_map.items():
        if pid not in chosen: db.delete(row)
    for pid in chosen:
        if pid not in existing_map:
            db.add(RolePermission(role_id=role_id,permission_id=pid,created_by=user.user_id))
    audit(db,user,'UPDATE','Role_Permissions',role_id,new={'permission_ids':sorted(chosen),'count':len(chosen)})
    db.commit(); db.close(); flash('تم حفظ مصفوفة الصلاحيات للدور المحدد.','ok'); return redirect(url_for('web.control',role_id=role_id))

@web.post('/control/role-permission')
def toggle_role_permission():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    role_id=request.form['role_id']; perm_id=request.form['permission_id']; row=db.get(RolePermission,(role_id,perm_id))
    if row: db.delete(row); action='DELETE'
    else: db.add(RolePermission(role_id=role_id,permission_id=perm_id,created_by=user.user_id)); action='CREATE'
    audit(db,user,action,'Role_Permissions',f'{role_id}:{perm_id}'); db.commit(); db.close(); return redirect(url_for('web.control'))

@web.post('/control/override')
def set_override():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    uid=request.form['user_id']; pid=request.form['permission_id']; effect=request.form['effect']
    row=db.scalar(select(UserPermissionOverride).where(UserPermissionOverride.user_id==uid,UserPermissionOverride.permission_id==pid))
    if not row:
        row=UserPermissionOverride(override_id=next_id(db,UserPermissionOverride,'override_id','OVR',6),user_id=uid,permission_id=pid,effect=effect,is_active=True,created_by=user.user_id,updated_by=user.user_id); db.add(row)
    else: row.effect=effect; row.is_active=True; row.updated_by=user.user_id
    audit(db,user,'UPSERT','User_Permission_Overrides',row.override_id,new={'user_id':uid,'permission_id':pid,'effect':effect}); db.commit(); db.close(); return redirect(url_for('web.control'))

@web.post('/control/scope')
def set_scope():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    uid=request.form['user_id']; sid=request.form['service_id']; st=datetime.strptime(request.form['start_date'],'%Y-%m-%d').date(); en=datetime.strptime(request.form['end_date'],'%Y-%m-%d').date()
    target=db.get(User,uid); role=db.get(Role,target.role_id) if target else None
    existing=db.scalars(select(UserServiceScope).where(UserServiceScope.user_id==uid)).all()
    maxn={'ADMIN':2,'SECRETARY':1,'ASSISTANT':1}.get(role.role_code if role else '',999)
    if not db.scalar(select(UserServiceScope).where(UserServiceScope.user_id==uid,UserServiceScope.service_id==sid)) and len(existing)>=maxn: flash('عدد الخدمات تجاوز الحد المسموح للدور.','error')
    elif db.scalar(select(UserServiceScope).where(UserServiceScope.user_id==uid,UserServiceScope.service_id==sid)): flash('النطاق موجود بالفعل.','info')
    else:
        sc=UserServiceScope(scope_id=next_id(db,UserServiceScope,'scope_id','SCP',6),user_id=uid,service_id=sid,start_date=st,end_date=en,created_by=user.user_id,updated_by=user.user_id); db.add(sc); audit(db,user,'CREATE','User_Service_Scopes',sc.scope_id,new={'user_id':uid,'service_id':sid,'start':str(st),'end':str(en)}); db.commit(); flash('تم إضافة Scope.','ok')
    db.close(); return redirect(url_for('web.control'))

@web.post('/control/security')
def update_security():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    s=db.get(SecuritySetting,1) or SecuritySetting(setting_id=1); db.add(s)
    s.otp_validity_seconds=max(30,int(request.form['otp_validity_seconds'])); s.otp_max_attempts=max(1,int(request.form['otp_max_attempts'])); s.otp_lock_seconds=max(30,int(request.form['otp_lock_seconds'])); s.revision_no=(s.revision_no or 0)+1; s.updated_by=user.user_id
    audit(db,user,'UPDATE','Security_Settings','1',new={'otp_validity_seconds':s.otp_validity_seconds,'otp_max_attempts':s.otp_max_attempts,'otp_lock_seconds':s.otp_lock_seconds,'revision_no':s.revision_no}); db.commit(); db.close(); flash('تم تحديث إعدادات OTP.','ok'); return redirect(url_for('web.control'))

@web.post('/control/user/create')
def create_user():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user): abort(403)
    username=request.form['username'].strip(); email=request.form['email'].strip(); password=request.form['password']; role_id=request.form['role_id']
    min_password_len=12 if current_app.config.get('APP_ENV') == 'production' else 8
    if len(password) < min_password_len:
        flash(f'كلمة المرور يجب ألا تقل عن {min_password_len} حرفًا.','error')
    elif db.scalar(select(User).where(or_(User.username==username,User.email==email))): flash('Username أو Email مستخدم بالفعل.','error')
    else:
        u=User(user_id=next_id(db,User,'user_id','U',3),username=username,email=email,password_hash=hash_password(password),role_id=role_id,is_active=True); db.add(u); audit(db,user,'CREATE','Users',u.user_id,new={'username':username,'role_id':role_id}); db.commit(); flash('تم إنشاء المستخدم.','ok')
    db.close(); return redirect(url_for('web.control'))

@web.post('/control/user/<user_id>/toggle')
def toggle_user(user_id):
    db=get_db(); user=current_user(db); target=db.get(User,user_id)
    if not user or not target or not is_super(db,user): abort(403)
    if target.user_id==user.user_id and target.is_active: flash('لا يمكن تعطيل Super Admin الحالي.','error')
    else: target.is_active=not target.is_active; audit(db,user,'UPDATE','Users',user_id,new={'is_active':target.is_active}); db.commit(); flash('تم تحديث حالة المستخدم.','ok')
    db.close(); return redirect(url_for('web.control'))

@web.post('/events/<event_id>/setup')
def setup_event(event_id):
    db=get_db(); user=current_user(db); ev=db.get(Event,event_id)
    if not ev or not is_super(db,user): abort(403)
    ev.affects_meeting=request.form.get('affects_meeting')=='1'
    mid=request.form.get('affected_meeting_id') or None
    if ev.affects_meeting:
        m=db.get(Meeting,mid)
        if not m or m.service_id!=ev.service_id or m.service_year_id!=ev.service_year_id or m.status!='COMPLETED': flash('Meeting غير صالحة للربط بالحدث.','error'); db.close(); return redirect(url_for('web.event_detail',event_id=event_id))
        ev.affected_meeting_id=mid
    else: ev.affected_meeting_id=None
    ev.updated_by=user.user_id; audit(db,user,'UPDATE','Events',ev.event_id,new={'affects_meeting':ev.affects_meeting,'affected_meeting_id':ev.affected_meeting_id}); db.commit(); flash('تم إعداد تأثير الحدث.','ok'); db.close(); return redirect(url_for('web.event_detail',event_id=event_id))

@web.post('/events/<event_id>/finalize-review')
def finalize_event_review(event_id):
    db=get_db(); user=current_user(db); ev=db.get(Event,event_id)
    if not ev or not ev.affected_meeting_id or not has_perm(db,user,'EDIT_EVALUATIONS'): abort(403)
    for e in db.scalars(select(Evaluation).where(Evaluation.event_id==event_id,Evaluation.evaluation_status=='SERVICE_EVENT_REVIEW')).all():
        e.evaluation_status='EVALUATED'; e.preparation_status=e.service_attendance_status=e.family_meeting_status='EVALUATED';
        if e.mass_attendance is not None: e.mass_attendance_status='EVALUATED'
        e.updated_by=user.user_id; e.updated_at=now()
    audit(db,user,'UPDATE','Events',event_id,new={'review_finalized':True}); db.commit(); db.close(); flash('تم اعتماد مراجعة الحدث.','ok'); return redirect(url_for('web.event_detail',event_id=event_id))


@web.post('/control/excel/apply')
def excel_apply():
    db=get_db(); user=current_user(db)
    if not user or not is_super(db,user) or not has_perm(db,user,'APPLY_EXCEL_CHANGES'): abort(403)
    changes=excel_detect(db,user); applied=0; rejected=0
    for fname,sheet,entity_id,op,old,new,diff in changes:
        try:
            model=EXCEL_SHEETS[sheet]
            with db.begin_nested():
                payload={k:v for k,v in new.items() if v not in (None,'') and hasattr(model,k)}
                pk=EXCEL_PKS[sheet]
                mapper=model.__mapper__
                pk_keys=[col.key for col in mapper.primary_key]
                identity=entity_id
                if len(pk_keys)>1 and isinstance(entity_id,str):
                    parts=entity_id.split(':', len(pk_keys)-1)
                    if len(parts)==len(pk_keys):
                        identity=tuple(parts)
                if op=='UPDATE' and entity_id:
                    obj=db.get(model,identity)
                    if not obj: raise ValueError('السجل غير موجود')
                    for k,v in payload.items():
                        if k in pk_keys: continue
                        if k in {'start_date','end_date','meeting_date','event_date','friday_date','effective_date'} and isinstance(v,str): v=datetime.fromisoformat(v).date()
                        setattr(obj,k,v)
                    audit(db,user,'EXCEL_APPLY_UPDATE',sheet,entity_id,old=old,new=payload)
                elif op=='INSERT':
                    if not entity_id:
                        if len(pk_keys)>1:
                            if not all(payload.get(k) not in (None,'') for k in pk_keys):
                                raise ValueError('المفتاح المركب غير مكتمل')
                            entity_id=':'.join(str(payload[k]) for k in pk_keys)
                        else:
                            prefix_map={Servant:('S',3),Service:('SV',3),ServiceYear:('SY',0),User:('U',3),Role:('R',3),Permission:('P',3),UserServiceScope:('SCP',6),ServiceAssignment:('ASN',6),ServiceTransfer:('TRF',6),Meeting:('MTG',6),Event:('EVT',6),Participant:('PAR',6),Evaluation:('EVAL',8),Excuse:('EXC',6),Opening:('OPN',6),FollowupRecord:('FUP',6)}
                            pref,dig=prefix_map[model]
                            entity_id=next_id(db,model,pk,pref,dig or 6) if model is not ServiceYear else payload.get(pk) or f"SY{date.today().year}-{date.today().year+1}"
                            payload[pk]=entity_id
                    if model is User:
                        payload['password_hash']=hash_password(str(payload.get('password_hash','changeme')))
                    obj=model(**payload); db.add(obj); db.flush(); audit(db,user,'EXCEL_APPLY_INSERT',sheet,entity_id,new=payload)
                else:
                    raise ValueError(f'Operation غير مدعومة: {op}')
            applied+=1
        except Exception as ex:
            rejected+=1
    db.commit(); db.close(); flash(f'تم تطبيق {applied} وتسجيل {rejected} تغييرات مرفوضة.','ok' if rejected==0 else 'info'); return redirect(url_for('web.excel_review'))
