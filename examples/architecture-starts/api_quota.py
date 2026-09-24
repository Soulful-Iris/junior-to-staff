"""Local mechanism demonstration for api-quota. No AWS resources are created."""
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE quota(org TEXT PRIMARY KEY,remaining INTEGER CHECK(remaining>=0))')
c.execute("INSERT INTO quota VALUES ('acme',1)")
for gateway in ('gateway-a','gateway-b'):
    allowed=c.execute('UPDATE quota SET remaining=remaining-1 WHERE org=? AND remaining>0',('acme',)).rowcount
    print(gateway,'allowed' if allowed else '429 quota exhausted')
print('remaining:',c.execute('SELECT remaining FROM quota').fetchone()[0])
