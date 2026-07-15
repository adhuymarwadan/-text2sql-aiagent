# test_guardrail.py — assert manual, jalankan: python test_guardrail.py
from guardrail import validate_sql


def ok(sql):
    passed, result = validate_sql(sql)
    assert passed, f"Harusnya lolos tapi ditolak: {sql!r} -> {result}"
    return result


def rejected(sql):
    passed, reason = validate_sql(sql)
    assert not passed, f"Harusnya ditolak tapi lolos: {sql!r} -> {reason}"


# --- harus lolos ---
ok("SELECT hostname, status FROM servers")
ok("SELECT s.hostname FROM servers s JOIN branches b ON s.branch_id = b.branch_id WHERE b.city = 'Balikpapan' AND s.status = 'offline'")
ok("SELECT count(*) FROM incidents WHERE status = 'open'")
ok("WITH x AS (SELECT server_id FROM status_logs) SELECT count(*) FROM x")  # CTE tetap lolos whitelist

# LIMIT 100 dipaksa kalau tidak ada, LIMIT user dipertahankan kalau ada
assert "LIMIT 100" in ok("SELECT * FROM servers")
assert "LIMIT 5" in ok("SELECT * FROM servers LIMIT 5")

# --- harus ditolak (skenario keamanan dari PROJECT_BRIEF) ---
rejected("DROP TABLE servers")
rejected("SELECT 1; DROP TABLE servers;")            # multiple statement injection
rejected("SELECT hostname FROM servers; DELETE FROM incidents;")
rejected("DELETE FROM servers WHERE status = 'offline'")
rejected("UPDATE servers SET status = 'online'")
rejected("INSERT INTO servers (hostname) VALUES ('x')")
rejected("TRUNCATE TABLE incidents")
rejected("ALTER TABLE servers ADD COLUMN x INT")
rejected("GRANT ALL ON servers TO public")
rejected("SELECT usename, passwd FROM pg_shadow")     # tabel sistem di luar whitelist
rejected("SELECT * FROM pg_catalog.pg_tables")
rejected("SELECT table_name FROM information_schema.tables")
rejected("")                                          # kosong
rejected("bukan sql sama sekali !!!")

print("Semua test guardrail LOLOS")
