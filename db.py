"""
db.py: A Python module for thread-safe SQLite database connections and transaction management.

Classes:
    SQLWrapper: A thread-safe wrapper for SQLite database connections that provides thread safety and transaction management.

"""

import sqlite3
import threading
import sys

## --- CLASSES ---

class SQLWrapper():
    """
    A thread-safe wrapper for SQLite database connections that provides thread safety and transaction management.

    Attributes:
        database (str): The name of the database file.
        _connection (sqlite3.Connection): The SQLite database connection.
        _cursor (sqlite3.Cursor): The SQLite database cursor.
        _lock (threading.Lock): A lock for thread safety.

    Methods:
        close(): Close the database connection.
    """

    def __init__(self, database):
        """
        Initialize a new SQLWrapper instance.

        Args:
            database (str): The name of the database file.
        """
        self.database = database
        if (sys.version_info.major == 3 and sys.version_info.minor >= 12): # 3.12 or later
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED", autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL)
        else:
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED")
        self._cursor = self._connection.cursor()
        self._lock = threading.Lock()

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            sqlite3.Cursor: The SQLite database cursor.
        """
        return self._connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context related to this object.

        Args:
            exc_type (Type[BaseException]): The type of the exception that caused the context to be exited, if any.
            exc_value (BaseException): The instance of the exception that caused the context to be exited, if any.
            traceback (traceback): A traceback object encapsulating the call stack at the point where the exception was raised, if any.
        """
        if exc_type is None:
            self._connection.commit()
        else:
            print(exc_type, exc_value, traceback)
            self._connection.rollback()
        self._cursor.close()

    def close(self):
        """
        Close the database connection.
        """
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None

## --- FUNCTIONS ---


def create_table(cursor, table_name, columns):
    pass

def drop_all_tables(cursor):
    with cursor:
        TABLES = ["example",
                  "example2"]
        for table in TABLES:
            cursor.execute("DROP TABLE IF EXISTS " + table)    

## --- MAIN ---
        
if __name__ == "__main__":

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
