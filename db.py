# db.py — koneksi & eksekusi query pakai role agent_readonly (read-only, timeout 5s).
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def execute_query(sql: str) -> dict:
    """Eksekusi query. Return {"ok": True, "columns", "rows"} atau {"ok": False, "error"}."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return {"ok": False, "error": "DATABASE_URL belum di-set di .env"}
    try:
        with psycopg.connect(url, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute(sql)
            columns = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchall() if cur.description else []
        return {"ok": True, "columns": columns, "rows": rows}
    except psycopg.Error as e:
        # ponytail: satu except psycopg.Error cukup — kolom salah, koneksi putus,
        # dan statement_timeout semua turunan kelas ini.
        return {"ok": False, "error": str(e).strip()}
