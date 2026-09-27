import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.seed import seed
seed()
print('Database initialized and bootstrap Super Admin is ready (credentials come from environment in production).')
