import sys
from helpers import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from rich.progress import track

try:
    Lista = open(sys.argv[1], "r").readlines()
except(IOError): 
    print("Error: Check your ip list path\n")
    sys.exit(1)

def task(line):
    simulating_task(line)

with ThreadPoolExecutor(50) as executor:
    fs = [executor.submit(task, line) for line in Lista]
    for i, f in enumerate(concurrent.futures.as_completed(fs)):
        sys.stdout.write("line nr: {} / {} \r".format(i, len(Lista)))

print("All task over!")