from colorama import Fore, Back, Style
import sys
import os
import subprocess
import requests
import time
import json
from time import sleep
import tldextract
import globals
from helpers import *
import db

GODADDY_TLDS = []

def godaddy_is_available(domain, max_retries=10):
    #print(Style.DIM + 'Checking domain %s with GoDaddy' % domain + Style.RESET_ALL)
    DOMAIN_API = "https://api.godaddy.com/v1/domains/available?domain="
    API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
    API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"
    
    request_url = DOMAIN_API + domain

    RATE_PER_MINUTE = 60

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url, headers = {
                    "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
                })
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    
                    if "available" in json_response:
                        #print("Available?: (GoDaddy)" + domain + ": " + str(json_response['available']))
                        return json_response['available'], json_response, request_url
                    else:
                        raise Exception("Missing available key in response")
                except ValueError:
                    raise Exception("Error in response")
            elif response.status_code == 429:
                print(f"GoDaddy Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 422:
                raise Exception("TLD not supported")
            else:
                print(f"Unexpected code {response.status_code}. Retrying (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)
            
        # Test
        sleep((60 / RATE_PER_MINUTE) * globals.NUM_THREADS)

    raise Exception(f"Failed to get response after {max_retries} attempts")

def domainsdb_is_available(domain, max_retries=10):
    #print(Style.DIM + 'Checking domain %s with DomainsDB' % domain + Style.RESET_ALL)
    DOMAIN_API = "https://api.domainsdb.info/v1/domains/search?domain="
    request_url = DOMAIN_API + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url)
            if response.status_code == 200:
                try:
                    json_response = response.json() 

                    if "domains" in json_response:
                        return False, "None"
                    else:
                        print(json_response)
                        raise Exception("Stuff broke")
                except ValueError:
                    raise Exception("Error in response")
            elif response.status_code == 429:
                print(f"DomainsDB Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 404:
                return True, "None"
            else:
                print(f"Unexpected code {response.status_code}. Retrying (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    raise Exception(f"Failed to get response after {max_retries} attempts")

def dns_query_naive(domain):
    import dns.resolver
    zone = {
        "NS",
        "A",
        "AAAA",
        "MX",
        "CNAME",
        "TXT",
        "SRV"
    }

    for record_type in zone:
        try:
            # timout 5 seconds

            resolver = dns.resolver.Resolver()

            dns_ns = random.choice(globals.DNS_SERVERS)
            #resolver.nameservers = [dns_ns]
            resolver.timeout = 15
            resolver.lifetime = 15

            answers = resolver.resolve(qname=domain, rdtype=record_type)

            if len(answers) != 0:
                # got some records
                return True
            else:
                raise Exception("This cant happen but it did so I'm throwing an exception with relevant information: " + record_type + " " + domain + " " + str(answers) + " " + dns_ns)
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.Timeout:
            print(Fore.RED + "Timeout on DNS server: " + dns_ns + Style.RESET_ALL)
            #raise Exception("Bad DNS server: " + dns_ns)
            # Instead of raising exception, continue to next DNS server because fuckit. The script will be slower but for now we don't care
            continue
        except Exception as e:
            raise e
    return False

# Will return True if we get NXDOMAIN, else False or raise Exeption.
# Exeption if we could not determine
# GUD JAG ÄR TRÖTT
def dns_nxdomain(domain):

    record_type = "NS"
        

    try:
        command = ['./zdns/zdns', record_type, '--verbosity', '1']
        result = subprocess.run(command, input=domain, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check if the command was successful
        if result.returncode == 0:
            response = json.loads(result.stdout)

            if "status" not in response:
                raise Exception("Go command failed: " + result.stdout)

            if (response["status"] == "NOERROR"):
                # We got a response, no need to continue
                return False
            
            if (response["status"] == "NXDOMAIN"):
                # We can assume the domain is available
                return True
            
            if (response["status"] == "SERVFAIL"):
                # We got a SERVFAIL, could not determine if domain is available
                return False
        else:
            # Print an error message if the command failed
            print(result.stderr)
            raise Exception("Command failed with return code:", result.returncode)
        # print exit code
    except Exception as e:
        raise e

# If domain is available, return True
def domain_analysis(url):
    
    # Debug request
    if False:
        API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
        API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"
                
                
        request_url = "https://api.godaddy.com/v1/domains/available?domain=codedrills.io"

        response = requests.get(request_url, headers = {
                "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
            })

        json_response = response.json()

        print(json_response)
    
    # If domain is full URL, extract domain
    
    domain_parts = tldextract.extract(url)

    if (domain_parts.suffix == ""):
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False    


    domain = domain_parts.domain + "." + domain_parts.suffix
    
    ## domaindb needs to update their stuff...
    if domain_parts.suffix == "to" or domain_parts == "ly":
        return False, "false"

    if domain in globals.checked_domains:
        return False, "false"

    ## You can write like this but god will punish you and you will suffer in hell for all eternity
    # return not dns_nxdomain(domain)

    try:
        if dns_nxdomain(domain):
            # dns query returned something
            return True, "dns"
    except Exception as e:
        raise e

    # If we get here, we could not determine if the domain is available with DNS query   
    
    
    
    with globals.checked_domains_lock:
        globals.checked_domains.add(domain)
    try:
        if domain_parts.suffix.upper() in globals.GODADDY_TLDS:
            pass
            return godaddy_is_available(domain), "godaddy"
        elif domain_parts.suffix.upper() in globals.DOMAINSDB_TLDS:
            return domainsdb_is_available(domain), "domaindb"
        else:
            pass
            #raise Exception("TLD not supported")

    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        raise e

    # If we get here, we could not determine if the domain is available with GoDaddy or DomainsDB
    raise Exception("Could not determine if domain is available: " + domain)


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
    #globals.GODADDY_TLDS = godaddy_get_supported_tlds()
    #globals.DOMAINSDB_TLDS = domainsdb_get_supported_tlds()

    url_file = "urlList"

    # read file and parse json
    with open(url_file, 'r') as file:
        
        # split each line
        lines = file.read().split('\n')
    

        for key in lines:
            # create dummy object
            dummy = DummyObject()
            
                        
            #a = domain_analysis(key)
            #print(a)
