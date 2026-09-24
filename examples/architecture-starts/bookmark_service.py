"""Local mechanism demonstration for bookmark-service. No AWS resources are created."""
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE bookmarks(owner TEXT,id INTEGER,title TEXT,version INTEGER,PRIMARY KEY(owner,id))')
c.execute("INSERT INTO bookmarks VALUES ('ana',7,'Original',3)")
for owner,title,version in [('ben','Unauthorized',3),('ana','Phone edit',3),('ana','Laptop edit',3)]:
    changed=c.execute('UPDATE bookmarks SET title=?,version=version+1 WHERE owner=? AND id=7 AND version=?',(title,owner,version)).rowcount
    print(owner,title,'saved' if changed else 'not found or version conflict')
print('Final:',c.execute('SELECT * FROM bookmarks').fetchall())
