"""Local mechanism demonstration for reading-list-it-works. No AWS resources are created."""
import sqlite3
c=sqlite3.connect(':memory:')
c.executescript('CREATE TABLE links(id INT PRIMARY KEY,owner TEXT,url TEXT,title TEXT); CREATE TABLE reads(user TEXT,link INT,is_read INT,PRIMARY KEY(user,link));')
c.execute('INSERT INTO links VALUES (?,?,?,?)',(7,'alice','https://example.invalid/guide',None))
c.executemany('INSERT INTO reads VALUES (?,?,?)',[('alice',7,1),('bob',7,0)])
print('Saved despite missing title:',c.execute('SELECT * FROM links').fetchall())
print('Personal progress:',c.execute('SELECT * FROM reads').fetchall())
