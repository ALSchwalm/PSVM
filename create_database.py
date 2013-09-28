from string import Formatter
import sqlite3
import hashlib

conn = sqlite3.connect('example.db')
c = conn.cursor()
c.executescript('''

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS comments;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY, 
    username TEXT COLLATE NOCASE, 
    pass_hash TEXT
);

CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    body TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
    ''')
    
user = ('user', hashlib.sha512("password").hexdigest())
c.execute('''INSERT INTO users VALUES(NULL, ?, ?)''', user)


# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
