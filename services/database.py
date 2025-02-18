import sqlite3
from config import Config

class Database:
    def __init__(self, db_name=Config.DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def query(self, sql, params=()):
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
