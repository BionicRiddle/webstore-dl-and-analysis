"""
db.py: A Python module for thread-safe SQLite database connections and transaction management.

Classes:
    SQLWrapper: A thread-safe wrapper for SQLite database connections that provides thread safety and transaction management.

"""

import sqlite3
import threading
import sys
from globals import DNS_RECORDS

if sqlite3.threadsafety == 0:
    raise Exception("sqlite3.threadsafety is 0. Program cannot continue as the sqlite3 module is not thread-safe. Needs to be 1 or 3. Check https://sqlite.org/threadsafe.html for more information.")

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
        
        #print(sqlite3.threadsafety)
        
        """
        Initialize a new SQLWrapper instance.

        Args:
            database (str): The name of the database file.
        """
        self.database = database
        if (sys.version_info.major == 3 and sys.version_info.minor >= 12): # 3.12 or later
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED", autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL, check_same_thread=False)
        else:
            self._connection = sqlite3.connect(database=self.database, isolation_level="DEFERRED", check_same_thread=False)
        self._cursor = self._connection.cursor()
        self._lock = threading.Lock()

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            sqlite3.Cursor: The SQLite database cursor.
        """
        with self._lock:
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
            #print("Committing transaction")
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

## Inserts

def insertDomainTable(sql_object, urlList, dns_record):
    # Insert the domain, extension and dns record type into the database
    
    insert = "INSERT INTO domain VALUES (?, ?, ?)"

    
    for url in urlList: 
        if dns_record[url] is not DNS_RECORDS.INVALID:
            # url: Self explanatory
            for extension in urlList[url]:
                # Extension: The extension and file the domain/url resides in
                # Todo: Maybe add check for duplicates, depending on if it's already fixed in
                try:
                    with sql_object as cursor:
                        # Invalid url
                        cursor.execute(insert, (url, extension[0], str(dns_record[url].value)))
                except sqlite3.Error as er:
                    print('SQLite error: %s' % (' '.join(er.args)))

def insertUrlTable(sqlobject, urls, dns_record): 
    # Insert the url & the times it is encountered into the database
    insert = "INSERT INTO common VALUES(?,?)"
    
    # Used to check for duplicates / remedy it
    select = "SELECT url FROM common WHERE url = ?"

    # Get amount of times url has occured (if it already exists in the database)
    getUrlCount = "SELECT count FROM common WHERE url = ?"
    
    # Update the number of times url has been encountered (if it already exists in the database)
    update = "UPDATE common SET count = ? WHERE url = ?"
    
    exists = None
    
    for url in urls:
        if url == "http://www.w3":
            print("Record: " + url)
            print(dns_record[url])
            print()
        if dns_record[url] is not DNS_RECORDS.INVALID:
        ## Check for dupliactes
            try:
                with sqlobject as cursor:
                    #query = select.format(url)
                    cursor.execute(select, (url,))
                    exists = cursor.fetchone()
            except sqlite3.Error as er:
                print('SQLite error: %s' % (' '.join(er.args)))
            
            # URL has already been added. Increment the existing one instead
            if exists:
                # Get current count
                try:
                    with sqlobject as cursor:
                        cursor.execute(getUrlCount, (url,))
                        count = cursor.fetchone()         
                except sqlite3.Error as er:
                    print('SQLite error: %s' % (' '.join(er.args)))
                
                # Update
                try:
                    with sqlobject as cursor:
                        cursor.execute(update, (int(count[0]+1), url))
                except sqlite3.Error as er:
                    print('SQLite error: %s' % (' '.join(er.args)))
                continue
                
            else:
                try:
                    with sqlobject as cursor:
                        cursor.execute(insert, (str(url), urls[url]))
                        
                except sqlite3.Error as er:
                    print('SQLite error: %s' % (' '.join(er.args)))
                  
def insertActionTable(sql_object, actionList, dns_record):
    
    
    # Queries
    select = "SELECT url, type, extension FROM action WHERE url = ? AND type = ? AND extension = ? AND filepath = ?"
    insert = "INSERT INTO action VALUES (?,?,?,?)"
    
    # Go through each action type (href, fetch, etc)
    
    for action in actionList:
        # action = href, fetch, etc
        # actionList[action]: domain followed by a list of extension
        for entry in actionList[action]:
            # Entry: Each indidual domain
            
            # Den får inget dns record, varför
            
            if dns_record[entry] is not DNS_RECORDS.INVALID:
                for extension in actionList[action][entry]:
                # actionList[action][entry]: List of extension(s) the domain resided in
                    try:
                        with sql_object as cursor:
                            # Check if domain already exists 
                            
                            # --- This may not be necessary --- #
                            # This check should already be done in each thread during keywordsearch and extension is unqieue per thread
                            # Will leave this here for now but might look back and reconsider later
                            
                            extensionId = extension.split("/")[0]
                            filePath = extension.split("/")[1]
                            print("filepath: " + str(filePath))
                            
                            cursor.execute(select, (entry, action, extensionId, filePath))
                            exists = cursor.fetchone()
                            # If entry does not exist
                            if exists == None:
                                cursor.execute(insert, (entry, action, extensionId, filePath))
                    except sqlite3.Error as er:
                        print('SQLite error: %s' % (' '.join(er.args)))

## Setup tables

def create_table(sql_object):
    with sql_object as cursor:
        #Domain Table
        cursor.execute("CREATE TABLE IF NOT EXISTS domain (url TEXT NOT NULL, extension TEXT NOT NULL, status TEXT, PRIMARY KEY (url,extension))")
        
        # Common Url Table
        cursor.execute("CREATE TABLE IF NOT EXISTS common (url TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY (url))")
        
        # Actions List
        # Components:
        # Action, Domain, Extension, (Domain should be primary)
        cursor.execute("CREATE TABLE IF NOT EXISTS action (url TEXT NOT NULL, type TEXT NOT NULL, extension TEXT NOT NULL, filepath TEXT NOT NULL, PRIMARY KEY (type, url, extension, filepath))")

def drop_all_tables(sql_object):
    with sql_object as cursor:
        TABLES = ["domain",
                  "common",
                  "action"]
        for table in TABLES:
            cursor.execute("DROP TABLE IF EXISTS " + table)    

## --- MAIN ---
        
if __name__ == "__main__":

    sql = SQLWrapper("thesis.db")

    # Stuff in Worker Thread example
    with sql as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS example (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO example (name) VALUES (?)", ("test",))

    with sql as cursor:
        cursor.execute("SELECT * FROM example")
        #print(cursor.fetchone())
        sql.commit()
        cursor.execute("SELECT * FROM example")
        #print(cursor.fetchone())
        #print(cursor.fetchone())
        #print(cursor.fetchone())

    # end of  program
    sql.close()
