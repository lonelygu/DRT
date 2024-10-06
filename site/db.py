import sqlite3
from settings import DB_NAME

conn = sqlite3.connect(DB_NAME)

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    truth INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER,
    fake_count INTEGER NOT NULL DEFAULT 0,
    not_fake_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (link_id) REFERENCES links(id)
)
''')

conn.commit()
conn.close()