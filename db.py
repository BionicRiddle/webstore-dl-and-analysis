"""Database helpers for the thesis SQLite store.

This module provides a thread-safe SQLite wrapper, insert helpers for domain,
domain metadata, common URLs, actions, and dynamic analysis results, plus
utilities for creating and dropping the database tables used by the analysis.
"""

import sqlite3
import sys
import threading
import traceback
from datetime import datetime

import globals
from globals import DNS_RECORDS
from helpers import get_valid_domain

if sqlite3.threadsafety == 0:
    raise Exception("sqlite3.threadsafety is 0. Program cannot continue as the sqlite3 module is not thread-safe. Needs to be 1 or 3. Check https://sqlite.org/threadsafe.html for more information.")

## --- CLASSES ---

class SQLWrapper():
    """Serialize access to a shared SQLite connection with context managers."""

    def __init__(self, database):
        """Initialize the shared SQLite connection for the given database file."""
        self.database = database
        if sys.version_info.major == 3 and sys.version_info.minor >= 12:  # 3.12 or later
            self._connection = sqlite3.connect(
                database=self.database,
                isolation_level="DEFERRED",
                autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL,
                check_same_thread=False,
            )
        else:
            self._connection = sqlite3.connect(
                database=self.database,
                isolation_level="DEFERRED",
                check_same_thread=False,
            )
        self._active_cursor = None
        self._lock = threading.Lock()

    def __enter__(self):
        """Acquire the connection lock and open a cursor for the transaction."""
        self._lock.acquire()
        try:
            self._active_cursor = self._connection.cursor()
            return self._active_cursor
        except Exception:
            self._lock.release()
            raise

    def __exit__(self, exc_type, exc_value, tb):
        """Commit or roll back the transaction, then close the active cursor."""
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                print(exc_type, exc_value, tb)
                self._connection.rollback()
        finally:
            if self._active_cursor is not None:
                self._active_cursor.close()
                self._active_cursor = None
            self._lock.release()

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
    """Insert RDAP and lifecycle metadata for a resolved domain."""
    insert = "INSERT INTO domain_meta (domain, status, expired, available, remove, raw_json) VALUES (?,?,?,?,?,?)"

    try:
        with sql_object as cursor:
            cursor.execute(insert, (domain, dns_status, expiration_date, available_date, deleted_date, rdap_dump))
    except sqlite3.Error as e:
        print("(insertDomainMetaTable) SQLite error: " + str(e))

def insertDomainTable(extension, sql_object, url, extension_path, file_path: str = ""):
    """Insert a domain hit for an extension version and source file path."""
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
    """Insert or increment common URL counters for URLs with valid DNS results."""
    if not globals.COMMON_URLS_ENABLE:
        return

    upsert = "INSERT INTO common (url, count) VALUES (?,1) ON CONFLICT(url) DO UPDATE SET count = count + 1"

    for url in urls:
        if dns_record.get(url) is DNS_RECORDS.INVALID:
            continue

        try:
            with sqlobject as cursor:
                cursor.execute(upsert, (str(url),))
        except sqlite3.Error as er:
            print(f"(insertUrlTable) SQLite error: {er}")
                  
def insertActionTable(extension, sql_object, actionList, dns_record):
    """Insert discovered extension actions while ignoring duplicate rows."""
    insert = "INSERT OR IGNORE INTO action (url, type, extension, version, filepath, domain, codeBefore) VALUES (?,?,?,?,?,?,?)"
    extension_id = extension.get_id()
    version = extension.get_version()

    for action in actionList:
        for entry in actionList[action]:
            domain, _ = get_valid_domain(entry)

            try:
                if dns_record[domain] is not DNS_RECORDS.INVALID:
                    for action_for_url in actionList[action][entry]:
                        file_path = action_for_url["filePath"]
                        context = action_for_url["context"]

                        with sql_object as cursor:
                            cursor.execute(insert, (entry, action, extension_id, version, file_path, domain, context))
            except sqlite3.Error as er:
                print('(insertActionTable) SQLite error: %s' % (' '.join(er.args)))
            except Exception as e:
                print("Error in insertActionTable: " + str(e))
                traceback.print_exc()

def insertDynamicTable(extension, sql_object, dynamicList):
    """Insert dynamic-analysis network events for an extension version."""
    with sql_object as cursor:
        insert = "INSERT INTO dynamic VALUES (?,?,?,?,?)"
        for entry in dynamicList:
            try:
                cursor.execute(insert, (entry["url"], entry["method"], entry["time_after_start"], extension.get_id(), extension.get_version()))
            except sqlite3.Error as er:
                print('(insertDynamicTable) SQLite error: %s' % (' '.join(er.args)))

## Setup tables

def create_table(sql_object):
    """Create all tables used by the analysis pipeline if they do not exist."""
    with sql_object as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS domain (domain TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, PRIMARY KEY (domain,extension,version,filepath))")
        cursor.execute("CREATE TABLE IF NOT EXISTS domain_meta (domain TEXT NOT NULL, status TEXT, expired DATETIME, available DATETIME, remove DATETIME, raw_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (timestamp,domain))")
        cursor.execute("CREATE TABLE IF NOT EXISTS common (url TEXT NOT NULL, count INTEGER NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url))")
        cursor.execute("CREATE TABLE IF NOT EXISTS dynamic (url TEXT NOT NULL, method TEXT NOT NULL, time_after_start FLOAT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url, method, extension, version))")
        cursor.execute("CREATE TABLE IF NOT EXISTS action (url TEXT NOT NULL, type TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, domain TEXT NOT NULL, codeBefore TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (type, url, extension, version, filepath), FOREIGN KEY (domain) REFERENCES domain(domain) )")

def drop_all_tables(sql_object):
    """Drop all analysis tables from the configured SQLite database."""
    print("Dropping tables")
    with sql_object as cursor:
        tables = ["domain", "domain_meta", "common", "action", "dynamic"]
        for table in tables:
            cursor.execute("DROP TABLE IF EXISTS " + table)
