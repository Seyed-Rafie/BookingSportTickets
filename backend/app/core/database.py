import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from app.core.config import settings

import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=settings.DATABASE_URL,
        # تنظیمات حیاتی TCP Keepalive برای Neon
        keepalives=1,
        keepalives_idle=30,       # بعد از ۳۰ ثانیه بی کاری، اولین پاکت Keepalive ارسال می‌شود
        keepalives_interval=10,   # اگر پاسخی نیامد، هر ۱۰ ثانیه دوباره تلاش می‌کند
        keepalives_count=5        # بعد از ۵ بار عدم پاسخ، اتصال را مرده فرض می‌کند
    )
    logger.info("Connected to Neon connection pool successfully.")
except Exception as e:
  logger.error(f"خطا در ساخت Pool: {e}")
  db_pool = None


@contextmanager
def get_db_connection(max_retries: int = 3):
    """مدیریت دریافت و بازگرداندن کانکشن از Pool.

    به همراه اعتبارسنجی کانکشن، تلاش مجدد (Retry) با وقفه (Backoff)، مدیریت
    Rollback و ثبت Logging.
    """
    if max_retries < 1:
        raise ValueError("مقدار max_retries باید حداقل ۱ باشد.")

    if db_pool is None:
        raise RuntimeError(
            "ارتباط با Database Pool برقرار نیست. لطفاً ابتدا db_pool را"
            " مقداردهی کنید."
        )

    conn = None

    for attempt in range(max_retries):
        try:
            conn = db_pool.getconn()

            # بررسی فعال بودن سوکت و زنده بودن کانکشن (مناسب برای Neon)
            with conn.cursor() as test_cursor:
                test_cursor.execute("SELECT 1;")

            # کانکشن سالم دریافت شد؛ خروج از حلقه تلاش مجدد
            break

        except (
            psycopg2.OperationalError,
            psycopg2.InterfaceError,
            psycopg2.DatabaseError,
        ) as e:
            logger.warning(
                "تلاش %d از %d برای دریافت کانکشن با خطا مواجه شد: %s",
                attempt + 1,
                max_retries,
                e,
            )
            if conn:
                try:
                    db_pool.putconn(conn, close=True)
                except Exception:
                    logger.exception(
                        "خطا در بستن و حذف کانکشن غیرفعال از Pool"
                    )
                conn = None

            if attempt == max_retries - 1:
                logger.error(
                    "عدم موفقیت در برقراری ارتباط با دیتابیس پس از %d تلاش.",
                    max_retries,
                )
                raise RuntimeError(
                    f"اتصال به دیتابیس پس از {max_retries} تلاش ناموفق بود:"
                    f" {e}"
                ) from e

            # ایجاد وقفه کوتاه پیش از تلاش مجدد (Backoff)
            time.sleep(0.5 * (attempt + 1))

    try:
        yield conn
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
                logger.info("تراکنش ناموفق با موفقیت Rollback شد.")
            except Exception:
                logger.exception("خطا در اجرای Rollback کانکشن")
        raise exc
    finally:
        if conn:
            try:
                db_pool.putconn(conn)
            except Exception:
                logger.exception("خطا در بازگرداندن کانکشن به Pool")


def execute_query(
    query: str,
    params: tuple | list | None = None,
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    """تابع جامع اجرای کوئری و بازگرداندن خروجی به‌صورت دیکشنری.

    :param query: دستور SQL برای اجرا
    :param params: پارامترهای کوئری برای جلوگیری از SQL Injection
    :param fetch_one: دریافت یک سطر خروجی (مناسب برای SELECT تکی)
    :param fetch_all: دریافت تمام سطرهای خروجی (مناسب برای SELECT دسته‌جمعی)
    :param commit: ثبت تغییرات در دیتابیس (برای INSERT, UPDATE, DELETE)
    """
    if fetch_one and fetch_all:
        raise ValueError(
            "پرچم‌های fetch_one و fetch_all نمی‌توانند به‌طور هم‌زمان True باشند."
        )

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
