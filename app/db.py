from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import DATABASE_URL, APP_ENV

is_sqlite = DATABASE_URL.startswith('sqlite')
connect_args = {'check_same_thread': False} if is_sqlite else {
    'connect_timeout': int(__import__('os').getenv('DB_CONNECT_TIMEOUT', '10'))
}

engine_kwargs = {
    'future': True,
    'pool_pre_ping': True,
    'connect_args': connect_args,
}

# PostgreSQL production defaults: recycle idle connections and keep the pool bounded.
if not is_sqlite:
    engine_kwargs.update({
        'pool_size': int(__import__('os').getenv('DB_POOL_SIZE', '5')),
        'max_overflow': int(__import__('os').getenv('DB_MAX_OVERFLOW', '10')),
        'pool_recycle': int(__import__('os').getenv('DB_POOL_RECYCLE', '1800')),
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    return SessionLocal()

def check_database():
    """Small connectivity check used by deployment/health tooling."""
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
        conn.commit()
    return True
