import sqlite3
from pathlib import Path
p=Path(r'C:/Users/imabh/OneDrive/Desktop/FDS4/db.sqlite3')
if not p.exists():
    print('db not found')
    raise SystemExit(1)
con=sqlite3.connect(str(p))
cur=con.cursor()
try:
    cur.execute('SELECT id,enrollment_no,first_name,last_name,email FROM students_student ORDER BY id DESC LIMIT 5')
    rows=cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('error',e)
finally:
    con.close()
