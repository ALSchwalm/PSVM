
import sqlite3

conn = sqlite3.connect('database.db', isolation_level=None)
conn.row_factory = sqlite3.Row
database = conn.cursor()