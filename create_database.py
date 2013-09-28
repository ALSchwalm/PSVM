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
    username TEXT NOT NULL COLLATE NOCASE, 
    pass_hash TEXT NOT NULL,
    email TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    body TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
    ''')
    
user = ('user', hashlib.sha512("password").hexdigest(), "invalid@gmail.com", True)
c.execute('''INSERT INTO users VALUES(NULL, ?, ?, ?, ?)''', user)


# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
