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
import pickle
import threading
import punycode
import traceback


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
    
    API_KEY = "0000000000000000"
    API_SECRET = "00000000000"
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

# Pickle save
def save_object(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

# Pickle load
def load_object(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Pickle Object
class SaveObject:
    def __init__(self, data):
        self.data = data

# Thread safe Unique Queue
class UniqueQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.unique_items = set()
        self.lock = threading.Lock()

    def save(self):
        not_done_items = []
        while not self.queue.empty():
            not_done_items.append(self.queue.get())

        return SaveObject([not_done_items, self.unique_items])

    def load(self, save):
        not_done_items = save.data[0]
        
        for item in not_done_items:
            self.put(item)
        
        # This will replace the unique items with the ones from the save
        self.unique_items = save.data[1]

    def put(self, item):
        with self.lock:
            if item not in self.unique_items:
                self.queue.put(item)
                self.unique_items.add(item)

    def get(self, block=True, timeout=None):
        with self.lock:
            item = self.queue.get(block, timeout)
            return item

    def empty(self):
        with self.lock:
            return self.queue.empty()

    def qsize(self):
        try:
            return self.queue.qsize()
        except:
            print("Could not get qsize")
            return -1

    def task_done(self):
        self.queue.task_done()

    def join(self):
        self.queue.join()

    def __len__(self):
        with self.lock:
            return len(self.queue)


def get_valid_domain(url):
    """
    Extracts the valid domain from a given URL. If non-ascii characters are present in the URL, they are converted to punycode.

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

    try:
            
        # add support for wildcard tlds, these are not actually valid tlds
        # and should be filtered out, but it is not a bad idea to keep for further analysis
        extract = tldextract.TLDExtract(extra_suffixes=["wildcardtld"])

        domain_parts = extract(url)
        domain = domain_parts.domain
        suffix = domain_parts.suffix

        # Here we filter out wildcards tlds and other invalid tlds
        disallowed_suffixes = ["google", "wildcardtld"]
        
        if domain == "www" or suffix in disallowed_suffixes or suffix == "" or domain == "":
            return None, None

        invalid_chars = ["_", ";", ":", " ", "!", "$", "%", "^", "&", "*", "(", ")", "+", "=", "[", "]", "{", "}", "\\", "|", "<", ">", ",", "`", "~", "'", "£"]
        for char in invalid_chars:
            if char in domain:
                print("Domain contains invalid char: " + domain)
                return None, None

        domain_puny = punycode.convert(domain, True)
        suffix_puny = punycode.convert(suffix, True)

        return ((domain_puny + "." + suffix_puny).lower(), suffix_puny.lower())
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("Could not get valid domain for url: " + url)
        print()
        return None, None

import queue
if __name__ == "__main__":
    test1 = "riddle.nu"
    test2 = "https://www.google.com"
    # url in russian
    test3 = "https://www.яндекс.рф"
    # chinese url
    test4 = "https://www.百度.中国"
    test5 = "dhjwkad"
    test6 = "телеока.рф"

    test7 = "https://www.google.com/as_asd"
    test8 = "https://www.goo_gle.com"
    test9 = "https://www.goo;gle.com"
    test10 = "https://www.goo gle.com"
    test11 = "https://www.goo,gle.com"


    reverse = "xn--80ajaudty.xn--p1ai"


    print(test1 + " " + str(get_valid_domain(test1)))
    print(test2 + " " + str(get_valid_domain(test2)))
    print(test3 + " " + str(get_valid_domain(test3)))
    print(test4 + " " + str(get_valid_domain(test4)))
    print(test5 + " " + str(get_valid_domain(test5)))
    print(test6 + " " + str(get_valid_domain(test6)))
    print(test7 + " " + str(get_valid_domain(test7)))
    print(test8 + " " + str(get_valid_domain(test8)))
    print(test9 + " " + str(get_valid_domain(test9)))
    print(test10 + " " + str(get_valid_domain(test10)))
    print(test11 + " " + str(get_valid_domain(test11)))

    assert get_valid_domain(reverse)[0] == reverse
    assert get_valid_domain(reverse)[1] == "xn--p1ai"
    assert get_valid_domain(test4)[0] != test4
    assert get_valid_domain(test1)[0] == "riddle.nu"

    print("All tests passed")