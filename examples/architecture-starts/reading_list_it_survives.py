"""Local mechanism demonstration for reading-list-it-survives. No AWS resources are created."""
import sqlite3
primary=sqlite3.connect(':memory:'); backup=sqlite3.connect(':memory:')
primary.execute('CREATE TABLE links(id INT PRIMARY KEY)')
primary.execute('INSERT INTO links VALUES (100)'); primary.commit(); primary.backup(backup)
primary.execute('INSERT INTO links VALUES (101)'); primary.commit()
print('Acknowledged primary:',primary.execute('SELECT id FROM links').fetchall())
print('Restored 12:00 snapshot:',backup.execute('SELECT id FROM links').fetchall())
print('Link 101 is absent: snapshot-only restore has acknowledged-write loss.')
