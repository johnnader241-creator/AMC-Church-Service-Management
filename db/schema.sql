
CREATE TABLE roles (
	role_id VARCHAR(30) NOT NULL, 
	role_code VARCHAR(50) NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	is_system_role BOOLEAN NOT NULL, 
	revision_no INTEGER NOT NULL, 
	PRIMARY KEY (role_id), 
	UNIQUE (role_code)
)

;


CREATE TABLE screens (
	screen_id VARCHAR(30) NOT NULL, 
	screen_code VARCHAR(50) NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (screen_id), 
	UNIQUE (screen_code)
)

;


CREATE TABLE servants (
	servant_id VARCHAR(10) NOT NULL, 
	name VARCHAR(250) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (servant_id), 
	CONSTRAINT ck_servant_status CHECK (status IN ('ACTIVE','INACTIVE'))
)

;


CREATE TABLE services (
	service_id VARCHAR(10) NOT NULL, 
	service_name VARCHAR(200) NOT NULL, 
	stage VARCHAR(200) NOT NULL, 
	day_of_week VARCHAR(10) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	opening_enabled BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (service_id), 
	CONSTRAINT ck_service_day CHECK (day_of_week IN ('THURSDAY','FRIDAY')), 
	CONSTRAINT ck_service_status CHECK (status IN ('ACTIVE','INACTIVE')), 
	UNIQUE (service_name)
)

;


CREATE TABLE followup_records (
	followup_id VARCHAR(30) NOT NULL, 
	servant_id VARCHAR(10), 
	servant_name_source VARCHAR(250), 
	beneficiary_name VARCHAR(250), 
	followup_date DATE, 
	method VARCHAR(100), 
	source VARCHAR(200), 
	import_batch_id VARCHAR(40), 
	imported_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (followup_id), 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT
)

;


CREATE TABLE permissions (
	permission_id VARCHAR(30) NOT NULL, 
	permission_code VARCHAR(80) NOT NULL, 
	permission_name VARCHAR(150) NOT NULL, 
	screen_id VARCHAR(30), 
	is_system_permission BOOLEAN NOT NULL, 
	PRIMARY KEY (permission_id), 
	UNIQUE (permission_code), 
	FOREIGN KEY(screen_id) REFERENCES screens (screen_id) ON DELETE RESTRICT
)

;


CREATE TABLE users (
	user_id VARCHAR(30) NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	email VARCHAR(200) NOT NULL, 
	password_hash TEXT NOT NULL, 
	role_id VARCHAR(30) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_login_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (user_id), 
	UNIQUE (username), 
	UNIQUE (email), 
	FOREIGN KEY(role_id) REFERENCES roles (role_id) ON DELETE RESTRICT
)

;


CREATE TABLE audit_log (
	log_id VARCHAR(40) NOT NULL, 
	user_id VARCHAR(30), 
	action VARCHAR(80) NOT NULL, 
	entity_type VARCHAR(80) NOT NULL, 
	entity_id VARCHAR(80), 
	old_value JSON, 
	new_value JSON, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (log_id), 
	CONSTRAINT ck_audit_entity_type CHECK (length(entity_type) > 0), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE excel_import_batches (
	batch_id VARCHAR(40) NOT NULL, 
	file_name VARCHAR(250) NOT NULL, 
	detected_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	detected_by VARCHAR(30), 
	status VARCHAR(30) NOT NULL, 
	total_rows INTEGER NOT NULL, 
	changed_rows INTEGER NOT NULL, 
	rejected_rows INTEGER NOT NULL, 
	applied_rows INTEGER NOT NULL, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (batch_id), 
	FOREIGN KEY(detected_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE otp_sessions (
	otp_session_id VARCHAR(30) NOT NULL, 
	user_id VARCHAR(30) NOT NULL, 
	issued_by VARCHAR(30) NOT NULL, 
	screen_code VARCHAR(50) NOT NULL, 
	otp_code VARCHAR(20) NOT NULL, 
	issued_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITHOUT TIME ZONE, 
	failed_at TIMESTAMP WITHOUT TIME ZONE, 
	attempt_count INTEGER NOT NULL, 
	last_attempt_at TIMESTAMP WITHOUT TIME ZONE, 
	lock_until TIMESTAMP WITHOUT TIME ZONE, 
	superseded_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(15) NOT NULL, 
	ip_address VARCHAR(80), 
	user_agent TEXT, 
	PRIMARY KEY (otp_session_id), 
	CONSTRAINT ck_otp_status CHECK (status IN ('ISSUED','USED','EXPIRED','FAILED')), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(issued_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE role_permissions (
	role_id VARCHAR(30) NOT NULL, 
	permission_id VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30), 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (role_id) ON DELETE RESTRICT, 
	FOREIGN KEY(permission_id) REFERENCES permissions (permission_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE role_screen_settings (
	role_id VARCHAR(30) NOT NULL, 
	screen_id VARCHAR(30) NOT NULL, 
	show_screen BOOLEAN NOT NULL, 
	can_view BOOLEAN NOT NULL, 
	can_edit BOOLEAN NOT NULL, 
	otp_required BOOLEAN NOT NULL, 
	revision_no INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30), 
	PRIMARY KEY (role_id, screen_id), 
	FOREIGN KEY(role_id) REFERENCES roles (role_id) ON DELETE RESTRICT, 
	FOREIGN KEY(screen_id) REFERENCES screens (screen_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE security_settings (
	setting_id INTEGER NOT NULL, 
	otp_validity_seconds INTEGER NOT NULL, 
	otp_max_attempts INTEGER NOT NULL, 
	otp_lock_seconds INTEGER NOT NULL, 
	revision_no INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30), 
	PRIMARY KEY (setting_id), 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE service_transfers (
	transfer_id VARCHAR(20) NOT NULL, 
	servant_id VARCHAR(10) NOT NULL, 
	from_service_id VARCHAR(10) NOT NULL, 
	to_service_id VARCHAR(10) NOT NULL, 
	effective_date DATE NOT NULL, 
	requested_by VARCHAR(30) NOT NULL, 
	requested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	destination_approved_by VARCHAR(30), 
	destination_approved_at TIMESTAMP WITHOUT TIME ZONE, 
	super_admin_approved_by VARCHAR(30), 
	super_admin_approved_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_by VARCHAR(30), 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(40) NOT NULL, 
	cancellation_reason TEXT, 
	emergency_reason TEXT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (transfer_id), 
	CONSTRAINT ck_transfer_status CHECK (status IN ('PENDING','DESTINATION_APPROVED','SUPER_ADMIN_APPROVED','COMPLETED','REJECTED','CANCELLED')), 
	CONSTRAINT ck_transfer_services CHECK (from_service_id <> to_service_id), 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT, 
	FOREIGN KEY(from_service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(to_service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(requested_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(destination_approved_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(super_admin_approved_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(completed_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE service_years (
	service_year_id VARCHAR(20) NOT NULL, 
	year_name VARCHAR(20) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	is_archived BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30), 
	updated_by VARCHAR(30), 
	PRIMARY KEY (service_year_id), 
	CONSTRAINT ck_year_dates CHECK (start_date <= end_date), 
	CONSTRAINT ck_year_status CHECK (status IN ('OPEN','CLOSED')), 
	UNIQUE (year_name), 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE trash_records (
	trash_id VARCHAR(30) NOT NULL, 
	entity_type VARCHAR(80) NOT NULL, 
	original_id VARCHAR(80) NOT NULL, 
	snapshot_data JSON NOT NULL, 
	deleted_by VARCHAR(30) NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	restore_count INTEGER NOT NULL, 
	last_restored_at TIMESTAMP WITHOUT TIME ZONE, 
	last_restored_by VARCHAR(30), 
	PRIMARY KEY (trash_id), 
	CONSTRAINT uq_trash_id UNIQUE (trash_id), 
	FOREIGN KEY(deleted_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(last_restored_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE user_permission_overrides (
	override_id VARCHAR(30) NOT NULL, 
	user_id VARCHAR(30) NOT NULL, 
	permission_id VARCHAR(30) NOT NULL, 
	effect VARCHAR(10) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30) NOT NULL, 
	updated_by VARCHAR(30) NOT NULL, 
	PRIMARY KEY (override_id), 
	CONSTRAINT uq_user_permission_override UNIQUE (user_id, permission_id), 
	CONSTRAINT ck_override_effect CHECK (effect IN ('ALLOW','DENY')), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(permission_id) REFERENCES permissions (permission_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE user_service_scopes (
	scope_id VARCHAR(30) NOT NULL, 
	user_id VARCHAR(30) NOT NULL, 
	service_id VARCHAR(10) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30), 
	updated_by VARCHAR(30), 
	PRIMARY KEY (scope_id), 
	CONSTRAINT uq_user_service_scope UNIQUE (user_id, service_id), 
	CONSTRAINT ck_scope_dates CHECK (start_date <= end_date), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE excel_change_staging (
	change_id VARCHAR(50) NOT NULL, 
	batch_id VARCHAR(40) NOT NULL, 
	file_name VARCHAR(250) NOT NULL, 
	sheet_name VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(80) NOT NULL, 
	entity_id VARCHAR(80), 
	operation VARCHAR(15) NOT NULL, 
	old_value JSON, 
	new_value JSON, 
	diff JSON, 
	validation_status VARCHAR(20) NOT NULL, 
	validation_message TEXT, 
	apply_status VARCHAR(20) NOT NULL, 
	applied_at TIMESTAMP WITHOUT TIME ZONE, 
	applied_by VARCHAR(30), 
	PRIMARY KEY (change_id), 
	FOREIGN KEY(batch_id) REFERENCES excel_import_batches (batch_id) ON DELETE RESTRICT, 
	FOREIGN KEY(applied_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE meetings (
	meeting_id VARCHAR(20) NOT NULL, 
	service_year_id VARCHAR(20) NOT NULL, 
	service_id VARCHAR(10) NOT NULL, 
	meeting_date DATE NOT NULL, 
	day_of_week VARCHAR(10) NOT NULL, 
	lesson_name TEXT, 
	status VARCHAR(30) NOT NULL, 
	generation_batch_id VARCHAR(50), 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_by VARCHAR(30), 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_by VARCHAR(30), 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30), 
	PRIMARY KEY (meeting_id), 
	CONSTRAINT uq_meeting_service_date UNIQUE (service_id, meeting_date), 
	CONSTRAINT ck_meeting_day CHECK (day_of_week IN ('THURSDAY','FRIDAY')), 
	CONSTRAINT ck_meeting_status CHECK (status IN ('SCHEDULED','COMPLETED','CANCELLED_BY_CHURCH','CANCELLED_BY_SERVICE')), 
	FOREIGN KEY(service_year_id) REFERENCES service_years (service_year_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(completed_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(cancelled_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE openings (
	opening_id VARCHAR(20) NOT NULL, 
	service_id VARCHAR(10) NOT NULL, 
	service_year_id VARCHAR(20) NOT NULL, 
	period_no INTEGER NOT NULL, 
	month INTEGER NOT NULL, 
	friday_date DATE NOT NULL, 
	link TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30) NOT NULL, 
	PRIMARY KEY (opening_id), 
	CONSTRAINT uq_opening_slot UNIQUE (service_id, service_year_id, period_no, month, friday_date), 
	CONSTRAINT ck_opening_period CHECK (period_no IN (1,2,3)), 
	CONSTRAINT ck_opening_month CHECK (month BETWEEN 1 AND 12), 
	FOREIGN KEY(service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_year_id) REFERENCES service_years (service_year_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE service_assignments (
	assignment_id VARCHAR(20) NOT NULL, 
	servant_id VARCHAR(10) NOT NULL, 
	service_id VARCHAR(10) NOT NULL, 
	service_year_id VARCHAR(20) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	reason TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30), 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30), 
	PRIMARY KEY (assignment_id), 
	CONSTRAINT ck_assignment_dates CHECK (start_date <= end_date), 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_year_id) REFERENCES service_years (service_year_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE events (
	event_id VARCHAR(20) NOT NULL, 
	service_id VARCHAR(10) NOT NULL, 
	service_year_id VARCHAR(20) NOT NULL, 
	event_name VARCHAR(250) NOT NULL, 
	event_date DATE NOT NULL, 
	event_type VARCHAR(30) NOT NULL, 
	affects_meeting BOOLEAN NOT NULL, 
	affected_meeting_id VARCHAR(20), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30) NOT NULL, 
	PRIMARY KEY (event_id), 
	CONSTRAINT uq_event_service_date UNIQUE (service_id, event_date), 
	CONSTRAINT fk_event_affected_meeting_same_service_year FOREIGN KEY(affected_meeting_id, service_id, service_year_id) REFERENCES meetings (meeting_id, service_id, service_year_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_event_type CHECK (event_type IN ('CONFERENCE','TRIP','PROJECT','SPORTS_DAY')), 
	FOREIGN KEY(service_id) REFERENCES services (service_id) ON DELETE RESTRICT, 
	FOREIGN KEY(service_year_id) REFERENCES service_years (service_year_id) ON DELETE RESTRICT, 
	FOREIGN KEY(affected_meeting_id) REFERENCES meetings (meeting_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE meeting_participants (
	participant_id VARCHAR(20) NOT NULL, 
	event_id VARCHAR(20) NOT NULL, 
	servant_id VARCHAR(10) NOT NULL, 
	participation_status VARCHAR(25) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(30) NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30) NOT NULL, 
	PRIMARY KEY (participant_id), 
	CONSTRAINT uq_event_participant UNIQUE (event_id, servant_id), 
	CONSTRAINT ck_participation_status CHECK (participation_status IN ('PARTICIPATED','NOT_PARTICIPATED')), 
	FOREIGN KEY(event_id) REFERENCES events (event_id) ON DELETE RESTRICT, 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE servant_meeting_evaluations (
	evaluation_id VARCHAR(40) NOT NULL, 
	meeting_id VARCHAR(20) NOT NULL, 
	servant_id VARCHAR(10) NOT NULL, 
	event_id VARCHAR(20), 
	preparation BOOLEAN, 
	preparation_status VARCHAR(30), 
	service_attendance BOOLEAN, 
	service_attendance_status VARCHAR(30), 
	family_meeting BOOLEAN, 
	family_meeting_status VARCHAR(30), 
	mass_attendance BOOLEAN, 
	mass_attendance_status VARCHAR(30), 
	evaluation_status VARCHAR(40) NOT NULL, 
	entered_by VARCHAR(30), 
	entered_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by VARCHAR(30), 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	archived_at TIMESTAMP WITHOUT TIME ZONE, 
	archived_by VARCHAR(30), 
	archive_reason VARCHAR(80), 
	excluded_reason VARCHAR(80), 
	excluded_note TEXT, 
	excluded_at TIMESTAMP WITHOUT TIME ZONE, 
	excluded_by VARCHAR(30), 
	PRIMARY KEY (evaluation_id), 
	CONSTRAINT uq_evaluation_meeting_servant UNIQUE (meeting_id, servant_id), 
	CONSTRAINT ck_evaluation_status CHECK (evaluation_status IN ('NOT_ENTERED','EVALUATED','EXCLUDED','SERVICE_EVENT_FULL','SERVICE_EVENT_REVIEW','EXCUSED','ARCHIVED')), 
	FOREIGN KEY(meeting_id) REFERENCES meetings (meeting_id) ON DELETE RESTRICT, 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT, 
	FOREIGN KEY(event_id) REFERENCES events (event_id) ON DELETE RESTRICT, 
	FOREIGN KEY(entered_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(updated_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(archived_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(excluded_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;


CREATE TABLE excuses (
	excuse_id VARCHAR(20) NOT NULL, 
	servant_id VARCHAR(10) NOT NULL, 
	meeting_id VARCHAR(20) NOT NULL, 
	evaluation_id VARCHAR(40), 
	reason TEXT NOT NULL, 
	status VARCHAR(15) NOT NULL, 
	submitted_by VARCHAR(30) NOT NULL, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	reviewed_by VARCHAR(30), 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	approval_note TEXT, 
	rejection_reason TEXT, 
	evaluation_snapshot JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (excuse_id), 
	CONSTRAINT ck_excuse_status CHECK (status IN ('PENDING','APPROVED','REJECTED')), 
	FOREIGN KEY(servant_id) REFERENCES servants (servant_id) ON DELETE RESTRICT, 
	FOREIGN KEY(meeting_id) REFERENCES meetings (meeting_id) ON DELETE RESTRICT, 
	FOREIGN KEY(evaluation_id) REFERENCES servant_meeting_evaluations (evaluation_id) ON DELETE RESTRICT, 
	FOREIGN KEY(submitted_by) REFERENCES users (user_id) ON DELETE RESTRICT, 
	FOREIGN KEY(reviewed_by) REFERENCES users (user_id) ON DELETE RESTRICT
)

;