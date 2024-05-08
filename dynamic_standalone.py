# This file is cursed. It is a standalone file that is used to run dynamic analysis on an extension.
import os
import time
import sqlite3
from colorama import Fore, Style
from helpers import *
from dynamic import dynamic_analysis
import globals
import db
import argparse
import threading
import traceback
from alive_progress import alive_bar

# Create a connection to the database
DATABASE = 'thesis.db'

# Create queue for threads
thread_queue = UniqueQueue()

# Start time
start_time = time.time()

# Count extensions
count_extensions = 0

# Worker Thread
class WorkerThread(threading.Thread):
    def __init__(self, queue, thread_id, sql):
        threading.Thread.__init__(self)

        self._queue = queue
        self._thread_id = thread_id
        self._stop_event = threading.Event()
        self._counter = 0
        self._current_extension = None

        self.sql = sql

    def run(self):
        print(Fore.YELLOW + 'Thread %d started' % self._thread_id + Style.RESET_ALL)

        # Wait for work to be added to the queue
        while self._queue.empty():
            if globals.TEMINATE:
                break
            time.sleep(1)
       
        while not self._stop_event.is_set():
            # Get the work from the queue, if done, terminate thread
            try:
                extension_path = self._queue.get(timeout=3)
            except queue.Empty as e:
                break
            try:
                if (globals.TEMINATE):
                    break
                self._current_extension = Extension(extension_path)
                try:
                    done = dynamic_analysis(self._current_extension)
                except Exception as e:
                    traceback.print_exc()
                    print(Fore.RED + 'Error in dynamic analysis: %s' % e + Style.RESET_ALL)
                    done = False
                dynamic_analysis_results = self._current_extension.get_dynamic_analysis()

                for entry in dynamic_analysis_results:
                    c.execute("INSERT INTO dynamic (url, method, time_after_start, extension, version) VALUES (?,?,?,?,?)", (entry['url'], entry['method'], entry['time_after_start'], self._current_extension.get_id(), self._current_extension.get_version()))

                if not done:
                    # If the extension exited early
                    print(Fore.RED + 'Extension %s exited early' % self._current_extension.get_id() + Style.RESET_ALL)
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

class Extension:
    def __init__(self, crx_path: str) -> None:
        try: 
            self.creation_time = time.time()
            self.crx_path = crx_path
            self.id = crx_path.split('/')[-2]
            self.version = ".".join(crx_path.split('.')[0].split('_')[-4:])
      
            self.dynamic_analysis = []
        except Exception as e:
            reason = "Error in 'Extension.__init__'"
            failed_extension(crx_path, reason, e)
            raise Exception("Failed to create Extension object")

    def set_dynamic_analysis(self, dynamic_analysis) -> None:
        self.dynamic_analysis = dynamic_analysis
    
    def get_crx_path(self) -> str:
        return self.crx_path

    def get_version(self) -> str:
        return self.version
    
    def get_dynamic_analysis(self) -> dict:
        return self.dynamic_analysis

    def get_id(self) -> str:
        return self.id

    def age(self) -> float:
        return time.time() - self.creation_time
    
    def __str__(self) -> str:
        return self.crx_path

def parse_arguments():
    parser = argparse.ArgumentParser(
        description = """
Extension analyzer

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden
""", 
        epilog = '''
Optional environment variables:
DISPLAY_PORT: N (default: 99)
    ''',
    formatter_class = argparse.RawTextHelpFormatter
    )

    # Optional arguments
    parser.add_argument('-t', '--threads',          type=int,               help="Number of threads to use",            default=globals.NUM_THREADS)
    parser.add_argument('-s', '--stfu',             action='store_true',    help="Disable Progress Bar",                default=globals.STFU_MODE)
    return parser.parse_args()

# CREATE TABLE domain_meta (domain TEXT NOT NULL, status TEXT, expired DATETIME, available DATETIME, remove DATETIME, raw_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (timestamp,domain))

# CREATE TABLE domain (domain TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, PRIMARY KEY (domain,extension,version,filepath))

# CREATE TABLE dynamic (url TEXT NOT NULL, method TEXT NOT NULL, time_after_start FLOAT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url, method, extension, version))


if __name__ == "__main__":
    args = parse_arguments()

    print(Fore.GREEN + 'Starting dynamic analysis with %d threads' % args.threads + Style.RESET_ALL)

    # Set number of threads
    globals.NUM_THREADS = args.threads
    globals.STFU_MODE = args.stfu

    # load DB thesis.db
    conn = sqlite3.connect('thesis.db')
    c = conn.cursor()

    # Get all extension paths
    extension_paths = []

    # load list of NXDOMAIN domains
    c.execute("SELECT DISTINCT d.extension FROM domain d JOIN domain_meta dm ON d.domain = dm.domain WHERE dm.status = 'NXDOMAIN' ORDER BY d.extension")

    extension_ids = c.fetchall()
    conn.close()

    root_path = "./extensions/"

    for extension_id in extension_ids[0]:
        extension_path = root_path + extension_id
        for crx in os.listdir(extension_path):
            if crx.endswith(".crx"):
                extension_paths.append(extension_path + '/' + crx)
    
    if len(extension_paths) == 0:
        print(Fore.RED + 'No extension path' + Style.RESET_ALL)
        sys.exit(1)
    
    builtins.print(
"""-------- Dynamic Extension analyzer V 1.0 --------

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden

--------------------------------------------------"""
    )

    # Stuff to do before starting threads

    # Load Pickle here?

    # Create a connection to the database using the SQLWrapper
    sql_w = db.SQLWrapper(DATABASE)
    esprima = None

    try:
        # Spawn and start threads
        threads = []
        for i in range(globals.NUM_THREADS):
            t = WorkerThread(thread_queue, i, sql_w)
            t.start()
            threads.append(t)
    except (Exception, KeyboardInterrupt) as e:
        pass

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

        # Save Queue state ?

        print(sum(counters), 'extensions analyzed')
        elapsed = time.time() - start_time
        print('Elapsed time: %s' % time.strftime("%H:%M:%S", time.gmtime(elapsed)))
        if exception is not None and int != 0:
            raise exception
        sys.exit(int)
    
    try:
        # add extensions to queue
        for extension_path in extension_paths:
            thread_queue.put(extension_path)
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

        print('Waiting for threads to finish...')
        
        # wait for all threads to finish or if the main thread is terminated, if main thread is terminated, terminate all threads
        thread_queue.join()
    except KeyboardInterrupt:
        print()
        print('Keyboard interrupt detected - terminating threads')
    exit(0)