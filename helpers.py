import sys
import random
import time
import builtins
from colorama import Fore, Back, Style
import globals
import requests

## Bara funktioner

def simulate_work(extension):
    time.sleep(random.uniform(0.1, 1))
    print(Style.DIM + ('Analyzed extension %s' % extension) + Style.RESET_ALL)

def print_old(*args, **kwargs):
    if not globals.STFU_MODE:
        builtins.print(*args, **kwargs)

#  exit with any args
def exit(*args, **kwargs):
    builtins.print(Fore.RED + "THIS SHOULD NOT BE CALLED" + Style.RESET_ALL)
    #raise Exception("exit() should not be called")
    sys.exit(*args, **kwargs)

def godaddy_get_supported_tlds():
    
    API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
    API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"
    DOMAIN_API = "https://api.godaddy.com/v1/domains/tlds"

    response = requests.get(DOMAIN_API, headers = {
        "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
    })

    json_response = response.json()

    tlds = []
    for tld in json_response:
        tlds.append(tld['name'].upper())

    return tlds

def domainsdb_get_supported_tlds():

    DOMAIN_API = "https://api.domainsdb.info/v1/info/tld/"

    response = requests.get(DOMAIN_API)

    json_response = response.json()

    tlds = []
    for tld in json_response["includes"]:
        tlds.append(tld.upper())

    return tlds
