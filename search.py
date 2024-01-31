import sys
import time
from datetime import datetime
import base64
import zipfile
import tempfile
import codecs
import json
import re, os, shutil
from tqdm import tqdm
import operator
import re
import threading
import queue

# Environment variables
PRETTY_OUTPUT       = os.getenv('PRETTY_OUTPUT'     , False)
RUN_ALL_VERSIONS    = os.getenv('RUN_ALL_VERSIONS'  , False)
DATE_FORMAT         = os.getenv('DATE_FORMAT'       , "%Y-%m-%d_%H:%M:%S")
NUM_THREADS         = os.getenv('NUM_THREADS'       , 1)

# Worker Thread
class WorkerThread(threading.Thread):
    def __init__(self, queue, thread_id):
        print('Starting thread %d' % thread_id)
        threading.Thread.__init__(self)
        self.queue = queue
        self.thread_id = thread_id
        self.stop_event = threading.Event()
        self.count = 0

    def run(self):
        while not self.stop_event.is_set():
            # Get the work from the queue and expand the tuple
            extension = self.queue.get()
            #analyze(extension)
            self.count += 1
            print('Thread %d: %d' % (self.thread_id, self.count))
            self.queue.task_done()

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
                    NUM_THREADS = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(NUM_THREADS)
                if arg in ['-a', '--all']:
                    RUN_ALL_VERSIONS = True
                    args.remove(arg)
                    args.remove(RUN_ALL_VERSIONS)
                if arg in ['-p', '--pretty']:
                    PRETTY_OUTPUT = True
                    args.remove(arg)
                    args.remove(PRETTY_OUTPUT)
                if arg in ['-d', '--date']:
                    DATE_FORMAT = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(DATE_FORMAT)
                if arg in ['-e', '--extension']:
                    extension = args[args.index(arg)+1]
                    args.remove(arg)
                    args.remove(extension)
                    print('Not implemented yet')
                    exit(1)
                if arg in ['-h', '--help']:
                    # I hate this
                    print('''
Usage: python3 search.py  [options] [path_to_extensions]
Example: python3 search.py extensions/

Optional arguments:
-h, --help: show this help message and exit
-t, --threads: number of threads to use
-a, --all: run all versions of each extension
-p, --pretty output: pretty print the output
-d, --date format: date format for output file
-e, --extension: run only one extension

Optional environment variables:
PRETTY_OUTPUT: True/False
RUN_ALL_VERSIONS: True/False
DATE_FORMAT: %Y-%m-%d_%H:%M:%S
NUM_THREADS: 1
                    ''')
                    exit(0)
        NUM_THREADS = int(NUM_THREADS)

    except Exception as e:
        print('Invalid arguments')
        print(e)
        exit(1)
    
    # I hate this too
    print(
"""------------ Extension analyzer V 1.0 ------------

Authors: Samuel Bach, Albin Karlsson 2024
Chalmers University of Technology, Gothenburg, Sweden

--------------------------------------------------"""
    )

    # Get path to extensions
    extensions_paths = [args[-1]] if len(args) > 1 else ['extensions/']
    for extensions_path in extensions_paths:
        if not os.path.isdir(extensions_path):
            print('Invalid path to extensions')
            exit(1)

    # Create queue
    queue = queue.Queue()

    # Spawn threads
    threads = []
    for i in range(NUM_THREADS):
        t = WorkerThread(queue, i)
        t.start()
        threads.append(t)

    # Scan and add extensions to queue
    extensions = []
    for extensions_path in extensions_paths:
        # for each dir in extensions_path
        for dir in os.listdir(extensions_path):
            versions = sorted([d for d in os.listdir(extensions_path + dir) if d[-4:] == ".crx"])
            if not versions:
                print("[+] Error (get_tmp_path) in {}: {}".format(file, 'OK') ) # TODO: Check if output format is important
                continue

            if RUN_ALL_VERSIONS:
                for version in versions:
                    extensions.append(extensions_path + dir + '/' + version)
            else:
                extensions.append(extensions_path + dir + '/' + versions[-1])



    max = 10
    i = 0
    # Analyze extensions by sending them to threads, when done, send next extension
    for extension in extensions:
        if i > max:
            break
        i += 1
        queue.put(extension)

    # Wait for all threads to finish
    print('Waiting for threads to finish...')

    # If terminated or done, signal threads to terminate
    try:
        queue.join()
    except KeyboardInterrupt:
        print('Terminating threads...')
        for t in threads:
            t.stop()
        print('Done')
        exit(0)