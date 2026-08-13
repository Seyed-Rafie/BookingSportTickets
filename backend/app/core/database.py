import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.core.config import settings

# ساخت استخر اتصالات با تنظیمات Keepalive برای جلوگیری از قطعی SSL در Neon
try:
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=settings.DATABASE_URL,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
    )
    print("connected to neon connection pool successfully")
except Exception as e:
    print(f"error with connection to neon: {e}")
    db_pool = None


@contextmanager
def get_db_connection():
    # دریافت و مدیریت خودکار کانکشن دیتابیس
    if db_pool is None:
        raise Exception("db_pool is None")
    
    conn = db_pool.getconn()
    
    # بررسی و سنجش زنده بودن کانکشن قبل از تحویل آن به برنامه
    try:
        if conn.closed != 0:
            db_pool.putconn(conn, close=True)
            conn = db_pool.getconn()
        else:
            # تست سریع برای اطمینان از فعال بودن سوکت SSL نئون
            with conn.cursor() as test_cursor:
                test_cursor.execute("SELECT 1;")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # اگر کانکشن قطع شده بود، آن را جایگزین می‌کنیم
        try:
            db_pool.putconn(conn, close=True)
        except Exception:
            pass
        conn = psycopg2.connect(
            settings.DATABASE_URL,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )

    try:
        yield conn
    finally:
        try:
            db_pool.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass


def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
    """
    function for run and return outputs of sql query
    outputs return in dict form
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                
                result = None
                if fetch_one:
                    row = cursor.fetchone()
                    result = dict(row) if row else None
                elif fetch_all:
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows] if rows else []

                if commit:
                    conn.commit()
                    
                return result
    except Exception as e:
        # اگر قطعی غیرمنتظره SSL رخ داد، یک بار دیگر با اتصال تازه تلاش کن
        if "SSL" in str(e) or "connection" in str(e).lower() or "closed" in str(e).lower():
            conn = psycopg2.connect(
                settings.DATABASE_URL,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params or ())
                    result = None
                    if fetch_one:
                        row = cursor.fetchone()
                        result = dict(row) if row else None
                    elif fetch_all:
                        rows = cursor.fetchall()
                        result = [dict(row) for row in rows] if rows else []
                    if commit:
                        conn.commit()
                    return result
            finally:
                conn.close()
        raise e


def check_db_health() -> bool:
    # check db health by running a simple query
    try:
        res = execute_query("SELECT 1 AS status;", fetch_one=True)
        return res is not None and res.get("status") == 1
    except Exception as e:
        print(f"error in db health check: {e}")
        return False
