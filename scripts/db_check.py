from app.db import check_database, DATABASE_URL

if __name__ == '__main__':
    check_database()
    safe = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL.split('://')[-1]
    print(f'Database connection OK: {safe}')
