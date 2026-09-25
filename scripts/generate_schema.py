import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from pathlib import Path
from app.db import Base
import app.models

out=[]
for table in Base.metadata.sorted_tables:
    out.append(str(CreateTable(table).compile(dialect=postgresql.dialect()))+';')
Path('db/schema.sql').write_text('\n\n'.join(out),encoding='utf-8')
print('generated db/schema.sql')