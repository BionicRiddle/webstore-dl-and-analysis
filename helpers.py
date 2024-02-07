import sys
import os
import random
import time
import builtins
from colorama import Fore, Back, Style

# Environment variables
PRETTY_OUTPUT       = os.getenv('PRETTY_OUTPUT'     , False)
RUN_ALL_VERSIONS    = os.getenv('RUN_ALL_VERSIONS'  , False)
DATE_FORMAT         = os.getenv('DATE_FORMAT'       , "%Y-%m-%d_%H:%M:%S")
NUM_THREADS         = os.getenv('NUM_THREADS'       , 1)
STFU_MODE           = os.getenv('STFU_MODE'         , False)

def simulate_work(extension):
    time.sleep(random.uniform(0.1, 1))
    print(Style.DIM + ('Analyzed extension %s' % extension) + Style.RESET_ALL)

def print(*args, **kwargs):
    if not STFU_MODE:
        builtins.print(*args, **kwargs)

##  exit with any args
def exit(*args, **kwargs):
    builtins.print(Fore.RED + "THIS SHOULD NOT BE CALLED" + Style.RESET_ALL)
    sys.exit(*args, **kwargs)