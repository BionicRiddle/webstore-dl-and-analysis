from colorama import Fore, Back, Style
import dns.resolver
import sys
import requests
import time
import json
from time import sleep
import tldextract
import globals
from helpers import *

GODADDY_TLDS = []

def godaddy_is_available(domain, max_retries=10):
    DOMAIN_API = "https://api.godaddy.com/v1/domains/available?domain="
    API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
    API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"
    
    request_url = DOMAIN_API + domain

    RATE_PER_MINUTE = 60

    for attempt in range(max_retries):
        sleep(60 / RATE_PER_MINUTE / globals.NUM_THREADS)
        try:
            response = requests.get(request_url, headers = {
                    "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
                })
            
            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "available" in json_response:
                        return "AVAILABLE" if json_response['available'] == True else "UNAVAILABLE"
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

def domainsdb_is_available(domain, max_retries=10):
    return "UNAVAILABLE"
    DOMAIN_API = "https://api.domainsdb.info/v1/domains/search?domain="
    request_url = DOMAIN_API + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url)
            if response.status_code == 200:
                try:
                    json_response = response.json() 

                    if "domains" in json_response:
                        return False
                    else:
                        print(json_response)
                        raise Exception("Stuff broke")
                except ValueError:
                    return "ERROR_IN_RESPONSE"
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 404:
                return "AVAILABLE"
            else:
                print(f"Unexpected code {response.status_code}. Retrying (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    raise Exception(f"Failed to get response after {max_retries} attempts")


# denna borde kanske inte returnera bool
def domain_analysis(url) -> bool:

    # If domain is full URL, extract domain
    domain_parts = tldextract.extract(url)

    #print(Fore.YELLOW + 'Analyzing domain: %s' % domain_parts + Style.RESET_ALL)

    if (domain_parts.suffix == ""):
        print(Fore.RED + 'No suffix found for domain: %s' % domain_parts.domain + Style.RESET_ALL)
        return False

    result = ""
    domain = domain_parts.domain + "." + domain_parts.suffix
    try:
        if domain_parts.suffix.upper() in globals.GODADDY_TLDS:
            print(Style.DIM + 'Checking domain %s with GoDaddy' % domain + Style.RESET_ALL)
            result = godaddy_is_available(domain)
        else:
            print(Style.DIM + 'Checking domain %s with DomainsDB' % domain + Style.RESET_ALL)
            exit()
            result = domainsdb_is_available(domain)

        match (result):
            case "MISSING_AVAILABLE":
                raise Exception("Missing available in response")
            case "ERROR_IN_RESPONSE":
                raise Exception("Error in response")
            case "TLD_NOT_SUPPORTED":
                raise Exception("TLD not supported")
            case "AVAILABLE":
                # Domain is not available for purchase
                return True
            case "UNAVAILABLE":
                pass
            case _:
                raise Exception("Unknown result")

    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        raise e

    # If we get here, we could not determine if the domain is available

    return False

    # TODO: Add DNS analysis

    zone = {
        "A":        [],
        "AAAA":     [],
        "MX":       [],
        "NS":       [],
        "CNAME":    []
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







if __name__ == "__main__":

    class DummyObject:
        def __init__(self) -> None:
            self.crx_path = "DUMMY_PATH"
        def get_keyword_analysis(self) -> dict:
            return {
                "list_of_urls":         [],
                "list_of_actions":      [],
                "list_of_common_urls":  []
            }

    # This is normally done in search.py before creating threads
    GODADDY_TLDS = godaddy_get_supported_tlds()

    url_file = "urlList"

    # read file and parse json
    with open(url_file, 'r') as file:
        data = file.read().replace('\n', '')
        
        json_data = json.loads(data)

        for key in json_data:
            # create dummy object
            dummy = DummyObject()
            domain_analysis(key)


