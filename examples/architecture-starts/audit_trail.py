"""Local mechanism demonstration for audit-trail. No AWS resources are created."""
import sqlite3,json
c=sqlite3.connect(':memory:')
c.executescript('CREATE TABLE permissions(id TEXT PRIMARY KEY,version INT,access TEXT); CREATE TABLE outbox(id TEXT PRIMARY KEY,payload TEXT);')
c.execute("INSERT INTO permissions VALUES ('report-7',1,'private')"); c.commit()
with c:
    c.execute("UPDATE permissions SET version=2,access='team' WHERE id='report-7' AND version=1")
    c.execute('INSERT INTO outbox VALUES (?,?)',('report-7:2',json.dumps({'actor':'ana','before':'private','after':'team'})))
print('After simulated crash before export:',c.execute('SELECT * FROM permissions').fetchall())
print('Still available to relay:',c.execute('SELECT * FROM outbox').fetchall())
