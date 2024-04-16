import os
import threading
from enum import Enum

# If True, this signals long running functions to terminate
TEMINATE = False

# If True, this signals the program to load the pickle file
PICKLE_LOAD = False

# Counter for the number of extensions that have been analyzed
extension_counter = 0

#Enums
class DNS_RECORDS(Enum):
    NOERROR  = "NOERROR"
    NXDOMAIN = "NXDOMAIN"
    SERVFAIL = "SERVFAIL"
    UNKNOWN  = "UNKNOWN"
    INVALID  = "INVALID"


# Bara globala variabler

# Environment variables
RUN_ALL_VERSIONS        = os.getenv('RUN_ALL_VERSIONS'          , False)
DATE_FORMAT             = os.getenv('DATE_FORMAT'               , "%Y-%m-%d_%H:%M:%S")
NUM_THREADS             = os.getenv('NUM_THREADS'               , 1)
STFU_MODE               = os.getenv('STFU_MODE'                 , False)
DROP_TABLES             = os.getenv('DROP_TABLES'               , False)
DEFAULT_EXTENSIONS_PATH = os.getenv('DEFAULT_EXTENSIONS_PATH'   , "extensions/")
NODE_PATH               = os.getenv("NODE_PATH"                 , "node")
NODE_APP_PATH           = os.getenv("NODE_APP_PATH"             , './node/app.js')
RANDOM_EXTENSION_ORDER  = os.getenv("RANDOM_EXTENSION_ORDER"    , False)
PICKLE_FILE             = os.getenv("PICKLE_FILE"               , "search.pkl")
DISPLAY_PORT            = os.getenv("DISPLAY_PORT"              , 99)

DNS_SERVERS = [
    "1.1.1.1",
    "1.0.0.1",
    "8.8.8.8",
    "8.8.4.4",
    "76.76.2.0",
    "76.76.10.0",
    "149.112.112.112",
    "208.67.222.222",
    "208.67.220.220",
    "185.228.168.9",
    "185.228.169.9",
    "94.140.14.14",
    "94.140.15.15"
]

GODADDY_TLDS = []
DOMAINSDB_TLDS = []
MISS_TLDS = ["name", "se", "jp", "cn", "ru", "io", "de", "no", "dk", "in", "ae", "eu", "net", "fi", "into", "link", "nu", "org", "com", "bg", "pt", "lv", "ae", "uk", "africa", "co.uk", "club", "co"]
RDAP_TLDS = []

# Domains
checked_domains = set()
checked_domains_lock = threading.Lock()

# DNS Records
dns_records = {}

# Variables for the static analysis
STATIC_ENABLE = os.getenv('STATIC_ENABLE', False)

# Variables and Environment variables for dynamic analysis
# TEMP
DYNAMIC_ENABLED = os.getenv('DYNAMIC_ENABLED', True)
os.environ['DISPLAY'] = f":{DISPLAY_PORT}"