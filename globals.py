"""Central configuration and shared runtime state for the extension analyzer.

This module collects environment-driven configuration together with mutable
cross-thread state used throughout the analysis pipeline.
"""

import os
import threading
from enum import Enum


def _bool_env(key: str, default: bool) -> bool:
    """Parse a boolean environment variable. Accepts 'true/false/1/0/yes/no/on/off'."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() not in ('0', 'false', 'no', 'off')


# If True, this signals long running functions to terminate
TERMINATE = False

# If True, this signals the program to load the pickle file
PICKLE_LOAD = False

# Counter for the number of extensions that have been analyzed
extension_counter = 0
extension_counter_lock = threading.Lock()


# Enums
class DNS_RECORDS(Enum):
    NOERROR = "NOERROR"
    NXDOMAIN = "NXDOMAIN"
    SERVFAIL = "SERVFAIL"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


# Shared configuration and runtime state
RUN_ALL_VERSIONS = _bool_env('RUN_ALL_VERSIONS', False)
DATE_FORMAT = os.getenv('DATE_FORMAT', "%Y-%m-%d_%H:%M:%S")
NUM_THREADS = int(os.getenv('NUM_THREADS', 1))
STFU_MODE = _bool_env('STFU_MODE', False)
DROP_TABLES = _bool_env('DROP_TABLES', False)
DEFAULT_EXTENSIONS_PATH = os.getenv('DEFAULT_EXTENSIONS_PATH', "extensions/")
NODE_PATH = os.getenv('NODE_PATH', "node")
NODE_APP_PATH = os.getenv('NODE_APP_PATH', './node/app.js')
RANDOM_EXTENSION_ORDER = _bool_env('RANDOM_EXTENSION_ORDER', False)
PICKLE_FILE = os.getenv('PICKLE_FILE', "search.pkl")
DISPLAY_PORT = int(os.getenv('DISPLAY_PORT', 99))
IN_DOCKER = _bool_env('IN_DOCKER', False)
DNS_ENABLE = _bool_env('DNS_ENABLE', True)
STATIC_ENABLE = _bool_env('STATIC_ENABLE', False)
RDAP_ENABLE = _bool_env('RDAP_ENABLE', False)
DYNAMIC_ENABLE = _bool_env('DYNAMIC_ENABLE', False)
COMMON_URLS_ENABLE = _bool_env('COMMON_URLS_ENABLE', False)
PRETTY_OUTPUT = _bool_env('PRETTY_OUTPUT', False)
DYNAMIC_WAIT_TIME = int(os.getenv('DYNAMIC_WAIT_TIME', 30))

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
    "94.140.15.15",
]

GODADDY_TLDS = []
DOMAINSDB_TLDS = []
# TLDs that are not supported by GoDaddy, DomainsDB or RDAP.
# TODO: integrate into domain_analysis.
MISS_TLDS = ["name", "se", "jp", "cn", "ru", "io", "de", "no", "dk", "in", "ae", "eu", "net", "fi", "into", "link", "nu", "org", "com", "bg", "pt", "lv", "ae", "uk", "africa", "co.uk", "club", "co"]
RDAP_TLDS = []

# Domains
checked_domains = set()
checked_domains_lock = threading.Lock()

# DNS records shared across worker threads
dns_records = {}
dns_records_lock = threading.Lock()

os.environ['DISPLAY'] = f":{DISPLAY_PORT}"
