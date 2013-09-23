from string import Formatter
import sqlite3
import hashlib

conn = sqlite3.connect('example.db')
c = conn.cursor()
c.executescript('''

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY, 
    username TEXT, 
    pass_hash TEXT)
    ''')
    
user = ('user', hashlib.sha512("password").hexdigest())
c.execute('''INSERT INTO users VALUES(NULL, ?, ?)''', user)


# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()