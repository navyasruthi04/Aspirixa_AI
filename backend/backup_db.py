import sqlite3, sys
from pathlib import Path

src = Path("database/aspirixa.db")
if not src.exists():
    sys.exit(f"NOT FOUND: {src.resolve()}  (run this from the Aspirixa_AI project root)")

dst = Path("database/aspirixa_backup_before_step1.db")
s = sqlite3.connect(src)
d = sqlite3.connect(dst)
s.backup(d)
d.close()
s.close()

def counts(path):
    c = sqlite3.connect(path)
    tables = [r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
    result = {t: c.execute(f'select count(*) from "{t}"').fetchone()[0] for t in tables}
    ok = c.execute("PRAGMA integrity_check").fetchone()[0]
    c.close()
    return ok, result

ok_src, a = counts(src)
ok_dst, b = counts(dst)
print("integrity source/backup:", ok_src, ok_dst)
print("row counts identical:", a == b)
for t, n in a.items():
    print(f"  {t}: {n}")