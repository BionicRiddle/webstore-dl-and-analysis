import sys
import time
from datetime import datetime
import base64
import tempfile
import codecs
import json
import re, os, shutil
from tqdm import tqdm
import operator
import re
import threading
import queue
import random
from analyze import analyze_extension
from colorama import Fore, Back, Style
import builtins
import globals
from helpers import *

# Create queue for threads
thread_queue = queue.Queue()

# Worker Thread
class WorkerThread(threading.Thread):
    def __init__(self, queue, thread_id):
        print('Starting thread %d' % thread_id)
        threading.Thread.__init__(self)
        self.queue = queue
        self.thread_id = thread_id
        self.stop_event = threading.Event()
        self.counter = 0
        self.current_temp = ""

    def run(self):
        while not self.stop_event.is_set():
            # Get the work from the queue, if done, terminate thread
            try:
                extension = self.queue.get(timeout=5)
            except queue.Empty as e:
                break
            try:
                analyze_extension(extension)
                #simulate_work(extension)
                self.counter += 1
            except Exception as e:
                print(Fore.RED + 'Error in thread %d: %s' % (self.thread_id, str(e)) + Style.RESET_ALL)
            self.queue.task_done()
        print(Fore.YELLOW + 'Thread %d terminated' % self.thread_id + Style.RESET_ALL)

    def get_thread_id(self):
        return self.thread_id

    def get_counter(self):
        return self.counter        

    def stop(self):
        self.stop_event.set()


if __name__ == "__main__":

    extension = None

    # list of args to be removed from when parsing
    args = sys.argv.copy()

    try:
        # optional arguments, exit if invalid
        if len(args) > 1:
            for arg in args:
                if arg in ['-t', '--threads']:
                    globals.NUM_THREADS = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(globals.NUM_THREADS)
                if arg in ['-s', '--stfu']:
                    helpers.STFU_MODE = True
                    args.remove(arg)
                if arg in ['-a', '--all']:
                    helpers.RUN_ALL_VERSIONS = True
                    args.remove(arg)
                if arg in ['-p', '--pretty']:
                    helpers.PRETTY_OUTPUT = True
                    args.remove(arg)
                if arg in ['-d', '--date']:
                    helpers.DATE_FORMAT = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(globals.DATE_FORMAT)
                if arg in ['-e', '--extension']:
                    extension = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(extension)
                if arg in ['-h', '--help']:
                    # I hate this
                    print('''
Usage: python3 search.py  [options] [path to extensions...]
Example: python3 search.py extensions/

Optional arguments:
-h, --help: show this help message and exit
-t, --threads: number of threads to use
-a, --all: run all versions of each extension
-p, --pretty output: pretty print the output
-d, --date format: date format for output file
-e, --extension: run only one extension
-s, --stfu: silent mode

Optional environment variables:
PRETTY_OUTPUT: True/False
RUN_ALL_VERSIONS: True/False
DATE_FORMAT: %Y-%m-%d_%H:%M:%S
NUM_THREADS: 1
                    ''')
                    sys.exit(0)
                try:
                    globals.NUM_THREADS = int(globals.NUM_THREADS)
                except:
                    raise Exception("Invalid number of threads: " + globals.NUM_THREADS)

        for arg in args:
            if arg[0] == '-':
                raise Exception("Invalid argument: " + arg)

    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        sys.exit(1)
    
    # I hate this too
    print(
"""------------ Extension analyzer V 1.0 ------------

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden

--------------------------------------------------"""
    )

    # Get path to extensions
    extensions_paths = []

    if extension is None:
        extensions_paths = [args[-1]] if len(args) > 1 else ['ext/']
        for extensions_path in extensions_paths:
            if not os.path.isdir(extensions_path):
                print(Fore.RED + 'Invalid path to extensions' + Style.RESET_ALL)
                sys.exit(1)
    else:
        globals.NUM_THREADS = 1

    # Stuff to do before starting threads
    # Get supported TLDs from GoDaddy
    globals.GODADDY_TLDS = godaddy_get_supported_tlds()

    # Spawn and start threads
    threads = []
    for i in range(globals.NUM_THREADS):
        t = WorkerThread(thread_queue, i)
        t.start()
        threads.append(t)

    def exit(int, exception=None):
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
        print(sum(counters), 'extensions analyzed')
        if exception is not None and int != 0:
            raise exception
        sys.exit(int)

    try:
        # Scan and add extensions to thread_queue
        count_extensions = 0
        if extension is not None:
            thread_queue.put(extension)
            count_extensions = 1
        else:
            for extensions_path in extensions_paths:
                # for each dir in extensions_path
                for dir in os.listdir(extensions_path):
                    versions = sorted([d for d in os.listdir(extensions_path + dir) if d[-4:] == ".crx"])
                    if not versions:
                        # Empty dir
                        print("[+] Error (get_tmp_path) in {}: {}".format(dir, 'OK') ) # TODO: Check if output format is important
                        continue

                    if globals.RUN_ALL_VERSIONS:
                        for version in versions:
                            thread_queue.put(extensions_path + dir + '/' + version)
                            count_extensions += 1
                    else:
                        thread_queue.put(extensions_path + dir + '/' + versions[-1])
                        count_extensions += 1
            print('Found %d extensions' % count_extensions)

        # Wait for all threads to finish
        print('Waiting for threads to finish...')

        # wait for all threads to finish or if the main thread is terminated, if main thread is terminated, terminate all threads
        thread_queue.join()

        # terminate all threads TODO: Kasnke onödig
        for t in threads:
            t.stop()
    except KeyboardInterrupt:
        print()
        print('Keyboard interrupt detected - terminating threads')

    exit(0)

    
    