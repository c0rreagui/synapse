import sqlite3
import os
import json

db_path = 'backend/synapse.db'
try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT metadata_info FROM schedule WHERE id = 1")
    row = cur.fetchone()
    if row:
        print("Metadata Dump:")
        print(row[0])
    con.close()
except Exception as e:
    print(e)
