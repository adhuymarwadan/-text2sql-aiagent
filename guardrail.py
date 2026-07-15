# guardrail.py — validasi SQL level sintaksis (AST), lapisan kritis sebelum DB.
import sqlglot
from sqlglot import exp

# Node terlarang di manapun dalam AST. hasattr guard karena nama kelas
# berbeda antar versi sqlglot (Alter vs AlterTable, dll).
_FORBIDDEN = tuple(
    getattr(exp, name)
    for name in (
        "Insert", "Delete", "Update", "Drop", "Alter", "AlterTable",
        "TruncateTable", "Create", "Command", "Grant", "Merge",
    )
    if hasattr(exp, name)
)

MAX_ROWS = 100

# Whitelist: hanya tabel aplikasi yang boleh disebut — blokir pg_catalog,
# information_schema, dan tabel sistem lain di level guardrail (bukan cuma GRANT).
ALLOWED_TABLES = {"branches", "servers", "status_logs", "incidents"}


def validate_sql(sql: str) -> tuple[bool, str]:
    """Return (True, sql_aman_dengan_LIMIT) kalau lolos, (False, alasan) kalau ditolak."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.ParseError as e:
        return False, f"SQL tidak bisa diparse: {e}"
    if len(statements) != 1:
        return False, "Hanya satu statement yang diizinkan (multiple statement ditolak)."
    stmt = statements[0]
    if not isinstance(stmt, (exp.Select, exp.Union)):
        return False, "Hanya query SELECT yang diizinkan."
    cte_names = {cte.alias_or_name.lower() for cte in stmt.find_all(exp.CTE)}
    for node in stmt.walk():
        if isinstance(node, _FORBIDDEN):
            return False, f"Perintah '{node.key.upper()}' tidak diizinkan."
        if isinstance(node, exp.Table) and node.name.lower() not in ALLOWED_TABLES | cte_names:
            return False, f"Tabel '{node.name}' tidak diizinkan."
    if stmt.args.get("limit") is None:
        stmt = stmt.limit(MAX_ROWS)
    return True, stmt.sql(dialect="postgres")
