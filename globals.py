import os

# Environment variables
PRETTY_OUTPUT       = os.getenv('PRETTY_OUTPUT'     , False)
RUN_ALL_VERSIONS    = os.getenv('RUN_ALL_VERSIONS'  , False)
DATE_FORMAT         = os.getenv('DATE_FORMAT'       , "%Y-%m-%d_%H:%M:%S")
NUM_THREADS         = os.getenv('NUM_THREADS'       , 1)
STFU_MODE           = os.getenv('STFU_MODE'         , False)

GODADDY_TLDS = []
