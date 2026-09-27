# Church Service System — Complete Fresh Start

This is the complete clean package for the Church Service management system.

## Start here
On Windows:

1. Extract the ZIP into a new folder.
2. Run `launch_fresh.bat`.
3. Open `http://localhost:5000`.
4. Login with the prepared Super Admin account.

The database shipped in `data/church_service.db` is already initialized from zero with the Super Admin configuration, so the first local launch does not depend on an old database.

## Production
Use PostgreSQL. Set `DATABASE_URL` and run `python scripts/bootstrap.py` or use Docker Compose.

## Main areas
Dashboard, Openings, Servants, Evaluations, Results, Events, Excuses, Transfers, Control Center, Database Explorer, Trash, Excel Review/Apply.

## Excel
Six workbooks are included under `excel/`.

Excel is a recovery/reference surface, not the source of truth. The intended flow is:

`Detect → Review → Diff → Apply`

Only Super Admin can Apply changes to the database.

## Branding
System name: **إدارة الخدمة**

Center name: **مركز افا موسي لتطوير التربيه الكنسيه**

Logo: `static/logo.png`

## Online deployment
راجع `DEPLOY_ONLINE_AR.md` و`render.yaml` للنشر على Render مع PostgreSQL.
