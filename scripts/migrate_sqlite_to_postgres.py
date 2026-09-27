"""One-time migration helper: copy all rows from the current SQLite DB to PostgreSQL.

Usage (from project root):
  APP_ENV=development python scripts/migrate_sqlite_to_postgres.py \
      --sqlite data/church_service.db \
      --postgres 'postgresql+psycopg://user:password@host:5432/church_service'

The destination schema is created from SQLAlchemy models. Existing destination rows
are NOT deleted; the script stops if a primary-key conflict is detected.
"""
import argparse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db import Base
import app.models as models

# Import all mapped classes so Base.metadata is complete.
_ = models

parser = argparse.ArgumentParser()
parser.add_argument('--sqlite', required=True)
parser.add_argument('--postgres', required=True)
args = parser.parse_args()

src = create_engine(f'sqlite:///{args.sqlite}', future=True)
dst = create_engine(args.postgres, future=True, pool_pre_ping=True)

Base.metadata.create_all(dst)

with Session(src) as ssrc, Session(dst) as sdst:
    tables = list(Base.metadata.sorted_tables)
    # Copy in FK-safe order. This preserves IDs, relationships, dates and JSON values.
    for table in tables:
        mapped = table.metadata.tables[table.name]
        rows = ssrc.execute(table.select()).mappings().all()
        if not rows:
            continue
        existing = sdst.execute(select(table)).mappings().all()
        existing_keys = {tuple(row[c.name] for c in table.primary_key.columns) for row in existing}
        new_rows = []
        for row in rows:
            key = tuple(row[c.name] for c in table.primary_key.columns)
            if key in existing_keys:
                raise RuntimeError(f'Primary-key conflict in {table.name}: {key}. Destination was not modified.')
            new_rows.append(dict(row))
        if new_rows:
            sdst.execute(table.insert(), new_rows)
            sdst.commit()
        print(f'{table.name}: {len(new_rows)} rows copied')

print('Migration completed successfully.')
