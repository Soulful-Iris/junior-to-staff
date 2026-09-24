"""Local mechanism demonstration for job-scheduler. No AWS resources are created."""
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE runs(schedule TEXT,version INT,due TEXT,state TEXT,PRIMARY KEY(schedule,version,due))')
for dispatcher in ('old-dispatcher','new-dispatcher'):
    changed=c.execute('INSERT OR IGNORE INTO runs VALUES (?,?,?,?)',('report-7',2,'2026-01-10T09:00:00Z','accepted')).rowcount
    print(dispatcher,'created run' if changed else 'existing run')
print(c.execute('SELECT * FROM runs').fetchall())
