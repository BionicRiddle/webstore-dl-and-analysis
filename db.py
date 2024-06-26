"""
db.py: A Python module for thread-safe SQLite database connections and transaction management.

Classes:
    SQLWrapper: A thread-safe wrapper for SQLite database connections that provides thread safety and transaction management.

"""

import sqlite3
import threading
import sys
from globals import DNS_RECORDS
from datetime import datetime
from helpers import get_valid_domain
import traceback

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

def insertDomainMetaTable(extension, sql_object, domain: str, dns_status: str, expiration_date: datetime, available_date: datetime, deleted_date: datetime, rdap_dump: str):
    #print("Inserting into domain_meta")
    insert = "INSERT INTO domain_meta (domain, status, expired, available, remove, raw_json) VALUES (?,?,?,?,?,?)"

    try:
        with sql_object as cursor:
            # Invalid url
            #print(dns_status)
            cursor.execute(insert, (domain, dns_status, expiration_date, available_date, deleted_date, rdap_dump))
    except sqlite3.Error as e:
        print("(insertDomainMetaTable) SQLite error: " + str(e))

def insertDomainTable(extension, sql_object, url,  extension_path, file_path="Funkar inte ATM"):
    
    insert = "INSERT OR IGNORE INTO domain (domain, extension, version, filepath) VALUES (?, ?, ?, ?)"

    extension_id = extension.get_id()
    version = extension.get_version()

    try:
        with sql_object as cursor:
            cursor.execute(insert, (url, extension_id, version, file_path))
    except sqlite3.IntegrityError as er:
        print("This should not happen because of the IGNORE statement")
    except sqlite3.Error as er:
        print("(insertDomainTable) SQLite error: %s" % (' '.join(er.args)))
        raise er

def insertUrlTable(extension, sqlobject, urls, dns_record): 
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
        if dns_record[url] is not DNS_RECORDS.INVALID:
            
        ## Check for dupliactes
            try:
                with sqlobject as cursor:
                    #query = select.format(url)
                    cursor.execute(select, (url,))
                    exists = cursor.fetchone()
            except sqlite3.Error as er:
                print('(insertUrlTable) SQLite error 1: %s' % (' '.join(er.args)))
            
            # URL has already been added. Increment the existing one instead
            if exists:
                # Get current count
                try:
                    with sqlobject as cursor:
                        cursor.execute(getUrlCount, (url,))
                        count = cursor.fetchone()         
                except sqlite3.Error as er:
                    print('(insertUrlTable) SQLite error 2: %s' % (' '.join(er.args)))
                
                # Update
                try:
                    with sqlobject as cursor:
                        cursor.execute(update, (int(count[0]+1), url))
                except sqlite3.Error as er:
                    print('(insertUrlTable) SQLite error 3: %s' % (' '.join(er.args)))
                continue
                
            else:
                try:
                    with sqlobject as cursor:
                        cursor.execute(insert, (str(url), urls[url]))
                        
                except sqlite3.Error as er:
                    print('(insertUrlTable) SQLite error 4: %s' % (' '.join(er.args)))
                  
def insertActionTable(extension, sql_object, actionList, dns_record):
    
    # Queries
    select = "SELECT url, type, extension FROM action WHERE url = ? AND type = ? AND extension = ? AND version = ? AND filepath = ?"
    insert = "INSERT INTO action (url, type, extension, version, filepath, domain, codeBefore) VALUES (?,?,?,?,?,?,?)"
    
    # Go through each action type (href, fetch, etc)
    
    for action in actionList:
        # action = href, fetch, etc
        # actionList[action]: domain followed by a list of extension
        for entry in actionList[action]:
            # Entry: Each indidual domain
            
            # Den får inget dns record, varför
            domain, tld = get_valid_domain(entry)

            try:
                if dns_record[domain] is not DNS_RECORDS.INVALID:
                    # Check if domain already exists 
                    
                    # --- This may not be necessary --- #
                    # This check should already be done in each thread during keywordsearch and extension is unqieue per thread
                    # Will leave this here for now but might look back and reconsider later
                    
                    extension_id = extension.get_id()
                    version = extension.get_version()

                    for action_for_url in actionList[action][entry]:
                        filePath = action_for_url["filePath"]
                        
                        context = action_for_url["context"]

                        #print("Filepath: " + str(filePath))
                        #print("Context: " + str(context))
                        with sql_object as cursor: # TODO: flytta in
                            cursor.execute(select, (entry, action, extension_id, version, filePath))
                            exists = cursor.fetchone()
                            # If entry does not exist
                            if exists == None:
                                cursor.execute(insert, (entry, action, extension_id, version, filePath, domain, context))
            except sqlite3.Error as er:
                print('(insertActionTable) SQLite error: %s' % (' '.join(er.args)))
            except Exception as e:
                print("Error in insertActionTable: " + str(e))
                traceback.print_exc()

def insertDynamicTable(extension, sql_object, dynamicList):
    with sql_object as cursor:
        insert = "INSERT INTO dynamic VALUES (?,?,?,?,?)"
        for entry in dynamicList:
            try:
                cursor.execute(insert, (entry["url"], entry["method"], entry["time_after_start"], extension.get_id(), extension.get_version()))
            except sqlite3.Error as er:
                print('(insertDynamicTable) SQLite error: %s' % (' '.join(er.args)))

## Setup tables

def create_table(sql_object):
    with sql_object as cursor:
        #Domain Table
        cursor.execute("CREATE TABLE IF NOT EXISTS domain (domain TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, PRIMARY KEY (domain,extension,version,filepath))")

        #Domain Meta Table
        cursor.execute("CREATE TABLE IF NOT EXISTS domain_meta (domain TEXT NOT NULL, status TEXT, expired DATETIME, available DATETIME, remove DATETIME, raw_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (timestamp,domain))")
        
        # Common Url Table
        cursor.execute("CREATE TABLE IF NOT EXISTS common (url TEXT NOT NULL, count INTEGER NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url))")

        # Dynamic Table
        cursor.execute("CREATE TABLE IF NOT EXISTS dynamic (url TEXT NOT NULL, method TEXT NOT NULL, time_after_start FLOAT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url, method, extension, version))")
        
        # Actions List
        # Components:
        # Action, Domain, Extension, (Domain should be primary)
        cursor.execute("CREATE TABLE IF NOT EXISTS action (url TEXT NOT NULL, type TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, domain TEXT NOT NULL, codeBefore TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (type, url, extension, version, filepath), FOREIGN KEY (domain) REFERENCES domain(domain) )")

def drop_all_tables(sql_object):
    print("Dropping tables")
    with sql_object as cursor:
        TABLES = ["domain",
                  "domain_meta",
                  "common",
                  "action",
                  "dynamic",]
        for table in TABLES:
            cursor.execute("DROP TABLE IF EXISTS " + table)    

## --- MAIN ---
        
if __name__ == "__main__":

    sql = SQLWrapper(globals.DATABASE)

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
