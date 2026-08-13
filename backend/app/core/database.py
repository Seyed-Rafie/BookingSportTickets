import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from app.core.config import settings

logger = logging.getLogger(__name__)

# ساخت ساده Pool
try:
  db_pool = ThreadedConnectionPool(1, 5, dsn=settings.DATABASE_URL)
except Exception as e:
  logger.error(f"خطا در ساخت Pool: {e}")
  db_pool = None


@contextmanager
def get_db_connection():
  if db_pool is None:
    raise RuntimeError("ارتباط با دیتابیس برقرار نیست.")

  conn = db_pool.getconn()

  # ۱. بررسی زنده بودن کانکشن (مخصوصاً برای Neon)
  try:
    with conn.cursor() as cur:
      cur.execute("SELECT 1;")
  except (psycopg2.OperationalError, psycopg2.InterfaceError):
    # اگر کانکشن قطع شده بود، آن را می‌بندیم و یکی جدید می‌گیریم
    db_pool.putconn(conn, close=True)
    conn = db_pool.getconn()

  # ۲. اجرای کوئری و مدیریت خطا
  try:
    yield conn
  except Exception:
    conn.rollback()  # لغو تغییرات در صورت بروز خطا
    raise
  finally:
    # ۳. بازگرداندن کانکشن به Pool
    if conn:
      db_pool.putconn(conn)


def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False,
):
  """تابع کمکی برای اجرای کوئری‌ها"""
  with get_db_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
      cursor.execute(query, params or ())
      result = None

      if fetch_one:
        row = cursor.fetchone()
        result = dict(row) if row else None
      elif fetch_all:
        rows = cursor.fetchall()
        result = [dict(r) for r in rows] if rows else []

      if commit:
        conn.commit()

      return result

def check_db_health() -> bool:
  """بررسی سلامت دیتابیس با اجرای یک کوئری ساده"""
  try:
    res = execute_query("SELECT 1 AS status;", fetch_one=True)
    # با isinstance به پایتون و Pylance ثابت می‌کنیم که res حتماً دیکشنری است
    return isinstance(res, dict) and res.get("status") == 1
  except Exception as e:
    logger.error(f"Error in DB health check: {e}")
    return False