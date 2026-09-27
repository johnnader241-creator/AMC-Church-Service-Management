# ERD — Fresh Start

```mermaid
erDiagram
  ROLES ||--o{ USERS : role
  ROLES ||--o{ ROLE_PERMISSIONS : grants
  PERMISSIONS ||--o{ ROLE_PERMISSIONS : assigned
  SCREENS ||--o{ PERMISSIONS : scopes
  ROLES ||--o{ ROLE_SCREEN_SETTINGS : configures
  SCREENS ||--o{ ROLE_SCREEN_SETTINGS : configures
  USERS ||--o{ USER_PERMISSION_OVERRIDES : overrides
  PERMISSIONS ||--o{ USER_PERMISSION_OVERRIDES : targets
  USERS ||--o{ USER_SERVICE_SCOPES : scopes
  SERVICES ||--o{ USER_SERVICE_SCOPES : visible_to
  SERVANTS ||--o{ SERVICE_ASSIGNMENTS : assigned
  SERVICES ||--o{ SERVICE_ASSIGNMENTS : receives
  SERVICE_YEARS ||--o{ SERVICE_ASSIGNMENTS : year
  SERVANTS ||--o{ SERVICE_TRANSFERS : moves
  SERVICES ||--o{ SERVICE_TRANSFERS : from
  SERVICES ||--o{ SERVICE_TRANSFERS : to
  SERVICE_YEARS ||--o{ MEETINGS : year
  SERVICES ||--o{ MEETINGS : hosts
  SERVICES ||--o{ EVENTS : owns
  SERVICE_YEARS ||--o{ EVENTS : year
  MEETINGS ||--o{ EVALUATIONS : receives
  SERVANTS ||--o{ EVALUATIONS : receives
  EVENTS ||--o{ EVALUATIONS : source
  EVENTS ||--o{ MEETING_PARTICIPANTS : has
  SERVANTS ||--o{ MEETING_PARTICIPANTS : joins
  SERVANTS ||--o{ EXCUSES : requests
  MEETINGS ||--o{ EXCUSES : covers
  EVALUATIONS ||--o{ EXCUSES : references
  SERVICES ||--o{ OPENINGS : owns
  SERVICE_YEARS ||--o{ OPENINGS : year
  USERS ||--o{ AUDIT_LOG : acts
  USERS ||--o{ OTP_SESSIONS : owns
  USERS ||--o{ TRASH_RECORDS : deletes
```
