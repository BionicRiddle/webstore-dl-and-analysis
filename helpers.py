import sys
import random
import time
import builtins
from colorama import Fore, Back, Style
import globals
import requests
import json
import tldextract
from datetime import datetime

## Bara funktioner

def simulate_work(extension):
    time.sleep(random.uniform(0.1, 1))
    print(Style.DIM + ('Analyzed extension %s' % extension) + Style.RESET_ALL)

def print(*args, **kwargs):
    builtins.print(datetime.now(), end=" - ")
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

def rdap_get_supported_tlds():
    DOMAIN_API = "https://root.rdap.org/domains"

    response = requests.get(DOMAIN_API)
    data = response.json()

    tlds = []
    for i in range(len(data["domainSearchResults"])):
        rem = data["domainSearchResults"][i]["remarks"]
        for j in range(len(rem)):
            if rem[j]["title"] == "RDAP Service":
                tlds.append(data["domainSearchResults"][i]["ldhName"])
    return tlds


def get_valid_domain(url):
    """
    Extracts the valid domain from a given URL.

    This function uses the tldextract library to extract the domain and suffix from the URL.
    It then checks if the domain or suffix is valid according to certain rules.
    If the domain is 'www', or the suffix is in a list of disallowed suffixes, or either the domain or suffix is empty, the function returns False.
    Otherwise, it returns the domain and suffix concatenated with a '.'.

    Parameters:
    url (str): The URL to extract the domain from.

    Returns:
    str|bool: The valid domain if it exists, otherwise False.

    Example:
    >>> get_valid_domain("https://www.google.com")
    'google.com'
    >>> get_valid_domain("https://www.ads")
    False
    """
    domain_parts = tldextract.extract(url)
    domain = domain_parts.domain
    suffix = domain_parts.suffix
    disallowed_suffixes = ["google"]
    
    if domain == "www" or suffix in disallowed_suffixes or suffix == "" or domain == "":
        return None, None

    return ((domain + "." + suffix).lower(), suffix.lower())

if __name__ == "__main__":
    raise Exception("This file is not meant to be run directly")