from colorama import Fore, Back, Style
import dns.resolver
import sys
import requests
import time
import json
from time import sleep
import tldextract

DOMAIN_API3 = "https://api.domainsdb.info/v1/domains/search?domain="
DOMAIN_API2 = "https://www.godaddy.com/en-uk/domainsearch/find?domainToCheck="

def godaddy_is_available(domain, max_retries=10):
    DOMAIN_API = "https://api.godaddy.com/v1/domains/available?domain="
    API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
    API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"
    
    request_url = DOMAIN_API + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url, headers = {
                    "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
                })
            
            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "available" in json:
                        return json['available']
                    else:
                        return "MISSING_AVAILABLE"
                except ValueError:
                    return "ERROR_IN_RESPONSE"
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 422:
                return "TLD_NOT_SUPPORTED"
            else:
                print(f"Unexpected code {response.status_code}. Retrying (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    raise Exception(f"Failed to get response after {max_retries} attempts")


def domain_analysis(url) -> bool:
    # If domain is full URL, extract domain
    domain = tldextract.extract(url)

    #print(Fore.YELLOW + 'Analyzing domain: %s' % domian + Style.RESET_ALL)

    if (domain.suffix == ""):
        print(Fore.RED + 'No suffix found for domain: %s' % domain.domain + Style.RESET_ALL)
        return False
    
    domain_api(domain.domain + "." + domain.suffix)
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


    