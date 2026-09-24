"""Local mechanism demonstration for url-shortener. No AWS resources are created."""
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE links(code TEXT PRIMARY KEY,target TEXT,expires INTEGER)')
for target in ('https://example.com/one','https://example.com/two'):
    try:
        c.execute('INSERT INTO links VALUES (?,?,?)',('launch',target,100))
        print('201 reserved launch for',target)
    except sqlite3.IntegrityError:
        print('409 alias already owned')
cached=c.execute('SELECT target,expires FROM links WHERE code=?',('launch',)).fetchone()
for now in (99,100,101):
    print('now',now,('302 '+cached[0]) if now<cached[1] else '410 expired')
