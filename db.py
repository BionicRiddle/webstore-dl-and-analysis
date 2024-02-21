import sqlite3
import threading
import sys


class SQLWrapper():
    def __init__(self, database):
        self.database = database
        if (sys.version_info.major == 3 and sys.version_info.minor >= 12): # 3.12 or later
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED", autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL)
        else:
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED")
        self._cursor = self._connection.cursor()
        self._lock = threading.Lock()

    def __enter__(self):
        return self._connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._connection.commit()
        else:
            print(exc_type, exc_value, traceback)
            self._connection.rollback()
        self._cursor.close()

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
        
    
# Init
sql = SQLWrapper("example.db")

# Stuff in Worker Thread example
with sql as cursor:
    cursor.execute("CREATE TABLE IF NOT EXISTS example (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO example (name) VALUES (?)", ("test",))

with sql as cursor:
    cursor.execute("SELECT * FROM example")
    print(cursor.fetchall())

# end of  program
sql.close()
