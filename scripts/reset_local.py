import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DATA_DIR
from app.seed import seed

p=DATA_DIR/'church_service.db'
if p.exists():
    try:
        p.unlink()
    except PermissionError as exc:
        print('ERROR: قاعدة البيانات ما زالت مستخدمة بواسطة البرنامج.')
        print('اقفل نافذة تشغيل النظام/السيرفر أولاً ثم شغّل reset_local.bat مرة أخرى.')
        print(f'File lock: {exc}')
        raise SystemExit(2)
seed()
print('Local database reset.')