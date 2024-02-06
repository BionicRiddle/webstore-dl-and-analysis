from colorama import Fore, Back, Style
import dns.resolver
import sys
import requests
import time
import json
from time import sleep

DOMAIN_API3 = "https://api.domainsdb.info/v1/domains/search?domain="
DOMAIN_API2 = "https://www.godaddy.com/en-uk/domainsearch/find?domainToCheck="

# OTE
# DOMAIN_API = "https://api.ote-godaddy.com/v1/domains/available?domain="
# API_KEY = "3mM44UdBYKmCkF_4dCRZpxNenyJ9HnayATmDt"
# API_SECRET = "FPvVjnyUCs2xtemxtHpu19"

# OTE
DOMAIN_API = "https://api.godaddy.com/v1/domains/available?domain="
API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"

delay = 0.0

def domain_api(domain):
    url = DOMAIN_API + domain
    global delay

    headers = {
        "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
    }
    sleep(1 + delay)

    time_start = time.time()
    response = requests.get(url, headers=headers)
    time_end = time.time()
    #print(Fore.YELLOW + 'API call took %f seconds' % (time_end - time_start) + Style.RESET_ALL)
    json = response.json()
    #print(json)

    if (response.status_code == 429):
        print(Fore.RED + 'Rate limit exceeded' + Style.RESET_ALL)
        delay += 0.2
        return

    if (response.status_code == 422):
        tld = domain.split('.')[-1].upper()
        print(Fore.RED + 'Domain TLD ".%s" is not supported (%s)' % (tld, domain) + Style.RESET_ALL)
        return

    if (response.status_code != 200):
        print(Fore.RED + 'Error code: %s' % response.status_code + Style.RESET_ALL)
        print(json)
        delay = delay/2
        return

    if "available" in json and json['available'] == True:
        print(Fore.GREEN + 'Domain %s is available' % domain + Style.RESET_ALL)
        # append to fiel hit.txt
        with open("hit.txt", "a") as file:
            file.write(domain + "\n")
    elif "available" in json and json['available'] == False:
        #print(Fore.RED + 'Domain %s is not available' % domain + Style.RESET_ALL)
        pass
    else:
        print(Fore.RED + 'Unknown response from API' + Style.RESET_ALL)

def domain_analysis(domian) -> bool:
    # If domain is full URL, extract domain
    if domian.startswith('http'):
        domian = '.'.join(domian.split('/')[2].split('.')[-2:])

    #print(Fore.YELLOW + 'Analyzing domain: %s' % domian + Style.RESET_ALL)
    
    domain_api(domian)
    return True

    zone = {
        "A": [],
        "AAAA": [],
        "MX": [],
        "NS": [],
        "CNAME": []
    }

    for record_type in zone:
        try:
            answers = dns.resolver.resolve(domian, record_type)
            for rdata in answers:
                zone[record_type].append(rdata.to_text())
        except Exception as e:
            print(Fore.RED + str(e) + Style.RESET_ALL)
            continue
    
    print(Fore.GREEN + 'Zone for %s' % domian + Style.RESET_ALL)
    for record_type in zone:
        print(Fore.GREEN + record_type + Style.RESET_ALL)
        for record in zone[record_type]:
            print('    ' + record)




class DummyObject:
    def __init__(self) -> None:
        self.crx_path = "DUMMY_PATH"
    def get_keyword_analysis(self) -> dict:
        return {
            "list_of_urls": [],
            "list_of_actions": [],
            "list_of_common_urls": []
        }

if __name__ == "__main__":

    url_file = "urlList"

    # read file and parse json
    with open(url_file, 'r') as file:
        data = file.read().replace('\n', '')
        
        json = json.loads(data)

        for key in json:
            # create dummy object
            dummy = DummyObject()

            domain_analysis(key)


    