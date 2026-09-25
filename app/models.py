from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint, JSON, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Role(Base):
    __tablename__='roles'
    role_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    role_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class Screen(Base):
    __tablename__='screens'
    screen_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    screen_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

class Permission(Base):
    __tablename__='permissions'
    permission_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    permission_name: Mapped[str] = mapped_column(String(150), nullable=False)
    screen_id: Mapped[str|None] = mapped_column(ForeignKey('screens.screen_id', ondelete='RESTRICT'))
    is_system_permission: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class RolePermission(Base):
    __tablename__='role_permissions'
    role_id: Mapped[str] = mapped_column(ForeignKey('roles.role_id', ondelete='RESTRICT'), primary_key=True)
    permission_id: Mapped[str] = mapped_column(ForeignKey('permissions.permission_id', ondelete='RESTRICT'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))

class RoleScreenSetting(Base):
    __tablename__='role_screen_settings'
    role_id: Mapped[str] = mapped_column(ForeignKey('roles.role_id', ondelete='RESTRICT'), primary_key=True)
    screen_id: Mapped[str] = mapped_column(ForeignKey('screens.screen_id', ondelete='RESTRICT'), primary_key=True)
    show_screen: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    otp_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))

class User(Base):
    __tablename__='users'
    user_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey('roles.role_id', ondelete='RESTRICT'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime|None] = mapped_column(DateTime)

class UserPermissionOverride(Base):
    __tablename__='user_permission_overrides'
    override_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    permission_id: Mapped[str] = mapped_column(ForeignKey('permissions.permission_id', ondelete='RESTRICT'), nullable=False)
    effect: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    updated_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    __table_args__=(UniqueConstraint('user_id','permission_id', name='uq_user_permission_override'), CheckConstraint("effect IN ('ALLOW','DENY')", name='ck_override_effect'))

class SecuritySetting(Base):
    __tablename__='security_settings'
    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    otp_validity_seconds: Mapped[int] = mapped_column(Integer, default=300)
    otp_max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    otp_lock_seconds: Mapped[int] = mapped_column(Integer, default=300)
    revision_no: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))

class Servant(Base):
    __tablename__='servants'
    servant_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default='ACTIVE', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(CheckConstraint("status IN ('ACTIVE','INACTIVE')", name='ck_servant_status'),)

class Service(Base):
    __tablename__='services'
    service_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    service_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    stage: Mapped[str] = mapped_column(String(200), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default='ACTIVE', nullable=False)
    opening_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(CheckConstraint("day_of_week IN ('THURSDAY','FRIDAY')", name='ck_service_day'), CheckConstraint("status IN ('ACTIVE','INACTIVE')", name='ck_service_status'))

class UserServiceScope(Base):
    __tablename__='user_service_scopes'
    scope_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(UniqueConstraint('user_id','service_id',name='uq_user_service_scope'), CheckConstraint('start_date <= end_date', name='ck_scope_dates'))

class ServiceYear(Base):
    __tablename__='service_years'
    service_year_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    year_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), default='OPEN', nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(CheckConstraint('start_date <= end_date', name='ck_year_dates'), CheckConstraint("status IN ('OPEN','CLOSED')", name='ck_year_status'))

class ServiceAssignment(Base):
    __tablename__='service_assignments'
    assignment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    servant_id: Mapped[str] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'), nullable=False)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    service_year_id: Mapped[str] = mapped_column(ForeignKey('service_years.service_year_id', ondelete='RESTRICT'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    reason: Mapped[str|None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(CheckConstraint('start_date <= end_date', name='ck_assignment_dates'),)

class ServiceTransfer(Base):
    __tablename__='service_transfers'
    transfer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    servant_id: Mapped[str] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'), nullable=False)
    from_service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    to_service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    effective_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    requested_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    destination_approved_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    destination_approved_at: Mapped[datetime|None] = mapped_column(DateTime)
    super_admin_approved_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    super_admin_approved_at: Mapped[datetime|None] = mapped_column(DateTime)
    completed_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    completed_at: Mapped[datetime|None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(40), default='PENDING', nullable=False)
    cancellation_reason: Mapped[str|None] = mapped_column(Text)
    emergency_reason: Mapped[str|None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(CheckConstraint("status IN ('PENDING','DESTINATION_APPROVED','SUPER_ADMIN_APPROVED','COMPLETED','REJECTED','CANCELLED')", name='ck_transfer_status'), CheckConstraint('from_service_id <> to_service_id', name='ck_transfer_services'))

class Meeting(Base):
    __tablename__='meetings'
    meeting_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    service_year_id: Mapped[str] = mapped_column(ForeignKey('service_years.service_year_id', ondelete='RESTRICT'), nullable=False)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    meeting_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)
    lesson_name: Mapped[str|None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='SCHEDULED', nullable=False)
    generation_batch_id: Mapped[str|None] = mapped_column(String(50))
    completed_at: Mapped[datetime|None] = mapped_column(DateTime)
    completed_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    cancelled_at: Mapped[datetime|None] = mapped_column(DateTime)
    cancelled_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(UniqueConstraint('service_id','meeting_date',name='uq_meeting_service_date'), CheckConstraint("day_of_week IN ('THURSDAY','FRIDAY')", name='ck_meeting_day'), CheckConstraint("status IN ('SCHEDULED','COMPLETED','CANCELLED_BY_CHURCH','CANCELLED_BY_SERVICE')", name='ck_meeting_status'))

class Event(Base):
    __tablename__='events'
    event_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    service_year_id: Mapped[str] = mapped_column(ForeignKey('service_years.service_year_id', ondelete='RESTRICT'), nullable=False)
    event_name: Mapped[str] = mapped_column(String(250), nullable=False)
    event_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    affects_meeting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    affected_meeting_id: Mapped[str|None] = mapped_column(ForeignKey('meetings.meeting_id', ondelete='RESTRICT'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    __table_args__=(UniqueConstraint('service_id','event_date',name='uq_event_service_date'), ForeignKeyConstraint(['affected_meeting_id','service_id','service_year_id'], ['meetings.meeting_id','meetings.service_id','meetings.service_year_id'], name='fk_event_affected_meeting_same_service_year', ondelete='RESTRICT'), CheckConstraint("event_type IN ('CONFERENCE','TRIP','PROJECT','SPORTS_DAY')", name='ck_event_type'))

class Participant(Base):
    __tablename__='meeting_participants'
    participant_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey('events.event_id', ondelete='RESTRICT'), nullable=False)
    servant_id: Mapped[str] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'), nullable=False)
    participation_status: Mapped[str] = mapped_column(String(25), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    __table_args__=(UniqueConstraint('event_id','servant_id',name='uq_event_participant'), CheckConstraint("participation_status IN ('PARTICIPATED','NOT_PARTICIPATED')", name='ck_participation_status'))

class Evaluation(Base):
    __tablename__='servant_meeting_evaluations'
    evaluation_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey('meetings.meeting_id', ondelete='RESTRICT'), nullable=False)
    servant_id: Mapped[str] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'), nullable=False)
    event_id: Mapped[str|None] = mapped_column(ForeignKey('events.event_id', ondelete='RESTRICT'))
    preparation: Mapped[bool|None] = mapped_column(Boolean)
    preparation_status: Mapped[str|None] = mapped_column(String(30))
    service_attendance: Mapped[bool|None] = mapped_column(Boolean)
    service_attendance_status: Mapped[str|None] = mapped_column(String(30))
    family_meeting: Mapped[bool|None] = mapped_column(Boolean)
    family_meeting_status: Mapped[str|None] = mapped_column(String(30))
    mass_attendance: Mapped[bool|None] = mapped_column(Boolean)
    mass_attendance_status: Mapped[str|None] = mapped_column(String(30))
    evaluation_status: Mapped[str] = mapped_column(String(40), default='NOT_ENTERED', nullable=False)
    entered_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    entered_at: Mapped[datetime|None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at: Mapped[datetime|None] = mapped_column(DateTime)
    archived_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    archive_reason: Mapped[str|None] = mapped_column(String(80))
    excluded_reason: Mapped[str|None] = mapped_column(String(80))
    excluded_note: Mapped[str|None] = mapped_column(Text)
    excluded_at: Mapped[datetime|None] = mapped_column(DateTime)
    excluded_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(UniqueConstraint('meeting_id','servant_id',name='uq_evaluation_meeting_servant'), CheckConstraint("evaluation_status IN ('NOT_ENTERED','EVALUATED','EXCLUDED','SERVICE_EVENT_FULL','SERVICE_EVENT_REVIEW','EXCUSED','ARCHIVED')", name='ck_evaluation_status'))

class Excuse(Base):
    __tablename__='excuses'
    excuse_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    servant_id: Mapped[str] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'), nullable=False)
    meeting_id: Mapped[str] = mapped_column(ForeignKey('meetings.meeting_id', ondelete='RESTRICT'), nullable=False)
    evaluation_id: Mapped[str|None] = mapped_column(ForeignKey('servant_meeting_evaluations.evaluation_id', ondelete='RESTRICT'))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default='PENDING', nullable=False)
    submitted_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    reviewed_at: Mapped[datetime|None] = mapped_column(DateTime)
    approved_at: Mapped[datetime|None] = mapped_column(DateTime)
    approval_note: Mapped[str|None] = mapped_column(Text)
    rejection_reason: Mapped[str|None] = mapped_column(Text)
    evaluation_snapshot: Mapped[dict|None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name='ck_excuse_status'),)

class Opening(Base):
    __tablename__='openings'
    opening_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    service_id: Mapped[str] = mapped_column(ForeignKey('services.service_id', ondelete='RESTRICT'), nullable=False)
    service_year_id: Mapped[str] = mapped_column(ForeignKey('service_years.service_year_id', ondelete='RESTRICT'), nullable=False)
    period_no: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    friday_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    __table_args__=(UniqueConstraint('service_id','service_year_id','period_no','month','friday_date',name='uq_opening_slot'), CheckConstraint('period_no IN (1,2,3)', name='ck_opening_period'), CheckConstraint('month BETWEEN 1 AND 12', name='ck_opening_month'))

class FollowupRecord(Base):
    __tablename__='followup_records'
    followup_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    servant_id: Mapped[str|None] = mapped_column(ForeignKey('servants.servant_id', ondelete='RESTRICT'))
    servant_name_source: Mapped[str|None] = mapped_column(String(250))
    beneficiary_name: Mapped[str|None] = mapped_column(String(250))
    followup_date: Mapped[datetime|None] = mapped_column(Date)
    method: Mapped[str|None] = mapped_column(String(100))
    source: Mapped[str|None] = mapped_column(String(200))
    import_batch_id: Mapped[str|None] = mapped_column(String(40))
    imported_at: Mapped[datetime|None] = mapped_column(DateTime)

class OTPSession(Base):
    __tablename__='otp_sessions'
    otp_session_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    issued_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    screen_code: Mapped[str] = mapped_column(String(50), nullable=False)
    otp_code: Mapped[str] = mapped_column(String(20), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime|None] = mapped_column(DateTime)
    failed_at: Mapped[datetime|None] = mapped_column(DateTime)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime|None] = mapped_column(DateTime)
    lock_until: Mapped[datetime|None] = mapped_column(DateTime)
    superseded_at: Mapped[datetime|None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(15), default='ISSUED', nullable=False)
    ip_address: Mapped[str|None] = mapped_column(String(80))
    user_agent: Mapped[str|None] = mapped_column(Text)
    __table_args__=(CheckConstraint("status IN ('ISSUED','USED','EXPIRED','FAILED')", name='ck_otp_status'),)

class AuditLog(Base):
    __tablename__='audit_log'
    log_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str|None] = mapped_column(String(80))
    old_value: Mapped[dict|None] = mapped_column(JSON)
    new_value: Mapped[dict|None] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__=(CheckConstraint("length(entity_type) > 0", name='ck_audit_entity_type'),)

class TrashRecord(Base):
    __tablename__='trash_records'
    trash_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    original_id: Mapped[str] = mapped_column(String(80), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    deleted_by: Mapped[str] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    restore_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_restored_at: Mapped[datetime|None] = mapped_column(DateTime)
    last_restored_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    __table_args__=(UniqueConstraint('trash_id', name='uq_trash_id'),)

class ExcelImportBatch(Base):
    __tablename__='excel_import_batches'
    batch_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detected_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(30), default='REVIEW')
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    changed_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    applied_rows: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime)

class ExcelChange(Base):
    __tablename__='excel_change_staging'
    change_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    batch_id: Mapped[str] = mapped_column(ForeignKey('excel_import_batches.batch_id', ondelete='RESTRICT'), nullable=False)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str|None] = mapped_column(String(80))
    operation: Mapped[str] = mapped_column(String(15), nullable=False)
    old_value: Mapped[dict|None] = mapped_column(JSON)
    new_value: Mapped[dict|None] = mapped_column(JSON)
    diff: Mapped[dict|None] = mapped_column(JSON)
    validation_status: Mapped[str] = mapped_column(String(20), default='PENDING')
    validation_message: Mapped[str|None] = mapped_column(Text)
    apply_status: Mapped[str] = mapped_column(String(20), default='PENDING')
    applied_at: Mapped[datetime|None] = mapped_column(DateTime)
    applied_by: Mapped[str|None] = mapped_column(ForeignKey('users.user_id', ondelete='RESTRICT'))
