from pathlib import Path
import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

APP_ENV = os.getenv('APP_ENV', 'development').lower()
_raw_db_url = os.getenv('DATABASE_URL', '').strip()

# SQLite is intentionally kept as the local-development default.
# Production/online deployments MUST provide PostgreSQL through DATABASE_URL.
if not _raw_db_url:
    if APP_ENV == 'production':
        raise RuntimeError('DATABASE_URL is required when APP_ENV=production. Use PostgreSQL.')
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'church_service.db'}"
else:
    DATABASE_URL = _raw_db_url

SECRET_KEY = os.getenv('SECRET_KEY', '').strip()
if APP_ENV == 'production' and (not SECRET_KEY or SECRET_KEY == 'CHANGE-ME-IN-PRODUCTION'):
    raise RuntimeError('A strong SECRET_KEY is required when APP_ENV=production.')
if not SECRET_KEY:
    SECRET_KEY = 'dev-only-change-me'

DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
APP_NAME = 'إدارة الخدمة'
CENTER_NAME = 'مركز افا موسي لتطوير التربيه الكنسيه'
BRAND_COLORS = {
    'maroon': '#6F1D2E', 'gold': '#9B670F', 'olive': '#526B4B',
    'paper': '#F7F4EF', 'ink': '#1F2937', 'muted': '#697386',
}

# Production session/security defaults
SESSION_COOKIE_SECURE = APP_ENV == 'production'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'church_service_session')
SESSION_LIFETIME_DAYS = max(1, int(os.getenv('SESSION_LIFETIME_DAYS', '14')))
PERMANENT_SESSION_LIFETIME = timedelta(days=SESSION_LIFETIME_DAYS)
