## --- IMPORTS ---

# System
import traceback
import sys
import os
import shutil
import time
import builtins
import re
from datetime import datetime
import zipfile
import argparse
import signal

# Concurrent threads
import threading
import queue

# CLI colors
from colorama import Fore, Back, Style

# Progress bar
from alive_progress import alive_bar

# Global variables and settings
import globals
from helpers import *

# Mutex SQLite Wrapper
import db

# Extension analysis
from analyze import analyze_extension

# Static analysis
from esprima import Esprima

## --- GLOBALS ---
extension_counter = 0
# Start time
start_time = time.time()

# Create queue for threads
thread_queue = UniqueQueue()

# Create a connection to the database
DATABASE = 'thesis.db'

def handle_sigterm(*args):
    print('SIGTERM detected - terminating threads')
    globals.TEMINATE = True
    raise KeyboardInterrupt()

signal.signal(signal.SIGTERM, handle_sigterm)

# Worker Thread
class WorkerThread(threading.Thread):
    def __init__(self, queue, thread_id, sql, esprima):
        print('Starting thread %d' % thread_id)
        threading.Thread.__init__(self)

        self._queue = queue
        self._thread_id = thread_id
        self._stop_event = threading.Event()
        self._counter = 0
        self._current_extension = None

        self.sql = sql
        self.esprima = esprima

    def run(self):

        # Wait for work to be added to the queue
        while self._queue.empty():
            if globals.TEMINATE:
                break
            time.sleep(1)
       
        while not self._stop_event.is_set():
            # Get the work from the queue, if done, terminate thread
            try:
                extension = self._queue.get(timeout=3)
            except queue.Empty as e:
                break
            try:
                if (globals.TEMINATE):
                    break
                self._current_extension = extension
                done = analyze_extension(self, extension)
                if not done:
                    # If the extension exited early, we need to put it back in the queue
                    self._queue.put(extension)
                self._current_extension = None
                self._counter += 1
            except Exception as e:
                traceback.print_exc()
                print(Fore.RED + 'Error in thread %d, cannot continue: %s' % (self._thread_id, e) + Style.RESET_ALL)
                # signal to all threads to terminate
                globals.TEMINATE = True
                break
            self._queue.task_done()
        print(Fore.YELLOW + 'Thread %d terminated' % self._thread_id + Style.RESET_ALL)

    def get_thread_id(self):
        return self._thread_id

    def get_counter(self):
        return self._counter

    def get_current_extension(self):
        return self._current_extension   

    def stop(self):
        self._stop_event.set()

def parse_arguments():
    parser = argparse.ArgumentParser(
        description = """
Extension analyzer

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden
""", 
        epilog = '''
Optional environment variables:
RUN_ALL_VERSIONS: True/False (default: False)
DATE_FORMAT: %Y-%m-%d_%H:%M:%S
NUM_THREADS: N (default: 1)
STFU_MODE: True/False (default: False)
DROP_TABLES: True/False (default: False)
DEFAULT_EXTENSIONS_PATH: "PATH" (default: "extensions/")
NODE_PATH: "PATH" (default: "node")
NODE_APP_PATH: "PATH" (default: "./node/app.js")
RANDOM_EXTENSION_ORDER: True/False (default: False)
PICKLE_FILE: "PATH" (default: "search.pkl")
DISPLAY_PORT: N (default: 99)
    ''',
    formatter_class = argparse.RawTextHelpFormatter
    )

    # Optional arguments
    parser.add_argument('-t', '--threads',          type=int,               help="Number of threads to use",            default=globals.NUM_THREADS)
    parser.add_argument('-a', '--all',              action='store_true',    help="Run all versions of each extension",  default=globals.RUN_ALL_VERSIONS)
    parser.add_argument('-d', '--date_format',      type=str,               help="Date format for output file",         default=globals.DATE_FORMAT)
    parser.add_argument('-e', '--extension',        type=str,               help="Run only one extension",              default=None)
    parser.add_argument('-s', '--stfu',             action='store_true',    help="Disable Progress Bar",                default=globals.STFU_MODE)
    parser.add_argument('-R', '--reset',            action='store_true',    help="Reset the database",                  default=globals.DROP_TABLES)
    parser.add_argument('-r', '--random',           action='store_true',    help="Randomize extension order",           default=globals.RANDOM_EXTENSION_ORDER)
    parser.add_argument('-p', '--pickle',           action='store_true',    help="Resume last state",                   default=False)
    
    # Positional argument
    parser.add_argument('path_to_extensions',       nargs='*',              help="Path to extensions",                  default=[globals.DEFAULT_EXTENSIONS_PATH])    
    return parser.parse_args()

if __name__ == "__main__":

    args = parse_arguments()

    # This is a bit stupid, but it works
    globals.NUM_THREADS = args.threads
    globals.RUN_ALL_VERSIONS = args.all
    globals.DATE_FORMAT = args.date_format
    globals.STFU_MODE = args.stfu
    globals.DROP_TABLES = args.reset
    globals.RANDOM_EXTENSION_ORDER = args.random
    globals.PICKLE_LOAD = args.pickle

    extensions_paths = args.path_to_extensions

    if args.extension is not None:
        globals.NUM_THREADS = 1

    if not extensions_paths and args.extension is None:
        print(Fore.RED + 'No extension path' + Style.RESET_ALL)
        sys.exit(1)

    for extensions_path in extensions_paths:
        if not os.path.isdir(extensions_path):
            print(extensions_path)
            print(Fore.RED + 'Invalid path to extensions' + Style.RESET_ALL)
            sys.exit(1)

    # I hate this too
    builtins.print(
"""------------ Extension analyzer V 1.0 ------------

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden

--------------------------------------------------"""
    )

    # Stuff to do before starting threads

    # Godaddy get supported TLDs
    if os.path.exists(os.getcwd() + "/GoDaddyCache.txt"):
        pass
    else:
        f = open("GoDaddyCache.txt", "w")
        f.write(str(godaddy_get_supported_tlds()))
        f.close()
    
    # DomainDb get supported TLDs
    if os.path.exists(os.getcwd() + "/DomainDbCache.txt"):
        pass
    else:
        f = open("DomainDbCache.txt", "w")
        f.write(str(domainsdb_get_supported_tlds()))
        f.close()

    # RDAP get supported TLDs
    if os.path.exists(os.getcwd() + "/RDAPCache.txt"):
        pass
    else:
        f = open("RDAPCache.txt", "w")
        f.write(str(rdap_get_supported_tlds()))
        f.close()
   
    # Read the cache files
    godaddy = open(os.getcwd() + "/GoDaddyCache.txt", "r")
    domaindb = open(os.getcwd() + "/DomainDbCache.txt", "r")
    rdap_tlds = open(os.getcwd() + "/RDAPCache.txt", "r")

    if globals.PICKLE_LOAD:
        print('Loading pickle file...')
        try:
            thread_queue.load(load_object(globals.PICKLE_FILE))
            print('Pickle file loaded')
        except:
            print(Fore.RED + 'Could not load pickle file' + Style.RESET_ALL)
            globals.PICKLE_LOAD = False
    
    globals.GODADDY_TLDS = godaddy.read()
    globals.DOMAINSDB_TLDS = domaindb.read()
    globals.RDAP_TLDS = rdap_tlds.read()

    # Create a connection to the database using the SQLWrapper
    sql_w = db.SQLWrapper(DATABASE)
    esprima = None
    if globals.STATIC_ENABLE:
        esprima = Esprima()
    try:

        # Drop tables if DROP_TABLES is set
        if globals.DROP_TABLES:
            db.drop_all_tables(sql_w)
        
        # Create tables if they don't exist
        db.create_table(sql_w)

        # Spawn and start threads
        threads = []
        for i in range(globals.NUM_THREADS):
            t = WorkerThread(thread_queue, i, sql_w, esprima)
            t.start()
            threads.append(t)
    except (Exception, KeyboardInterrupt) as e:
        if globals.STATIC_ENABLE:
            esprima.close_process()


    def exit(int, exception=None):
        globals.TEMINATE = True
        sql_w.close()
        counters = []
        for t in threads:
            t.stop()
        for t in threads:
            t.join()
            try:
                counters.append(t.get_counter())
            except:
                print(Fore.RED + ('Could not get counter from crashed thread %d' % t.get_thread_id() ) + Style.RESET_ALL)
        print('Threads terminated')
        print()

        if globals.STATIC_ENABLE:
            print('Closing Esprima process')
            esprima.close_process()
            print('Esprima process closed')
            print()

        print('Saving Queue state')
        save_object(thread_queue.save(), globals.PICKLE_FILE)
        print('Queue state saved')
        print()

        print(sum(counters), 'extensions analyzed')
        elapsed = time.time() - start_time
        print('Elapsed time: %s' % time.strftime("%H:%M:%S", time.gmtime(elapsed)))
        if exception is not None and int != 0:
            raise exception
        sys.exit(int)

    try:
        # Scan and add extensions to thread_queue
        count_extensions = 0
        if args.extension is not None:
            thread_queue.put(args.extension)
            count_extensions = 1
        else:
            for extensions_path in extensions_paths:
                # for each dir in extensions_path
                extension_path_list = os.listdir(extensions_path)

                if (globals.RANDOM_EXTENSION_ORDER):
                    import random
                    random.shuffle(extension_path_list)

                for dir in extension_path_list:
                    # If something is wrong while it is scanning the extensions, it will terminate all threads
                    if (globals.TEMINATE):
                        exit(0)
                    versions = sorted([d for d in os.listdir(extensions_path + dir) if d[-4:] == ".crx"])
                    if not versions:
                        # Empty dir
                        print(Fore.RED + 'No extensions found in %s' % dir + Style.RESET_ALL)
                        continue

                    if globals.RUN_ALL_VERSIONS:
                        for version in versions:
                            thread_queue.put(extensions_path + dir + '/' + version)
                            count_extensions += 1
                    else:
                        thread_queue.put(extensions_path + dir + '/' + versions[-1])
                        count_extensions += 1
            print('Found %d extensions' % count_extensions)

        if not globals.STFU_MODE:
            # progress bar using qsize, using alive_bar
            with alive_bar(count_extensions, bar='blocks', spinner='dots_waves', length=40, title='Analyzing extensions', manual=True) as bar:
                while not thread_queue.empty():
                    if (globals.TEMINATE):
                        exit(0)
                    item_progress = 1 - (thread_queue.qsize() / count_extensions)
                    bar(item_progress)
                    time.sleep(1)
                bar(1)
                
        # Wait for all threads to finish
        print('Waiting for threads to finish...')

        # wait for all threads to finish or if the main thread is terminated, if main thread is terminated, terminate all threads
        thread_queue.join()
    except KeyboardInterrupt:
        print()
        print('Keyboard interrupt detected - terminating threads')
    exit(0)
