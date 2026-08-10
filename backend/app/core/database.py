import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.core.config import settings

# ساخت استخر اتصالات (Connection Pool) برای دیتابیس Neon
# minconn=1: حداقل ۱ اتصال همیشه باز است
# maxconn=10: حداکثر ۱۰ اتصال هم‌زمان برای پاسخ‌دهی ایجاد می‌شود
try:
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=settings.DATABASE_URL
    )
    print("connected to neon connection pool successfully")
except Exception as e:
    print(f"error with connection to neon: {e}")
    db_pool = None


@contextmanager
def get_db_connection():
    # get and drop automatically connection
    if db_pool is None:
        raise Exception("db_pool is None")
    
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        # drop connection
        db_pool.putconn(conn)


def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
    """
    function for run and return outputs of sql query
    outputs return in dict form
    """
    with get_db_connection() as conn:
        # RealDictCursor is for returning output in dict form
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            
            result = None
            if fetch_one:
                row = cursor.fetchone()
                result = dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows] if rows else []

            # commit is necessary for insert, update, delete
            if commit:
                conn.commit()
                
            return result


def check_db_health() -> bool:
    # check db healt by run a simple query
    try:
        res = execute_query("SELECT 1 AS status;", fetch_one=True)
        return res is not None and res.get("status") == 1
    except Exception as e:
        print(f"error in db health check: {e}")
        return False