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
from globals import DNS_RECORDS
from helpers import *
import db


#Unoffcial API KEY (Samuel)
#Key: h1Jo22moy2n4_Wqi1sKQDBAzRYbPKDYuaoM
#Secret: QGRs57FnetX9qQsNVbXKeL

# curl -X 'GET' 'https://api.godaddy.com/v1/domains/available?domain=npms.io&checkType=FAST&forTransfer=true'  -H 'accept: application/json'   -H 'Authorization: sso-key h1Jo22moy2n4_Wqi1sKQDBAzRYbPKDYuaoM:QGRs57FnetX9qQsNVbXKeL'


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
                        return json_response['available']
                    else:
                        raise Exception("Missing available key in response")
                except ValueError:
                    raise Exception("Error in response")
            elif response.status_code == 429:
                print(f"GoDaddy Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 422:
                return False
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

def doubleCheck(url):
    
    domain_parts = tldextract.extract(url)

    if (domain_parts.suffix == ""):
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False    


    domain = domain_parts.domain + "." + domain_parts.suffix
    
    cookies = {
    'PHPSESSID': '08jmanir8f6fki7t0ka9b16n16',
    'intercom-id-al0g0fgs': 'fe6386ee-28f8-4392-a9bd-f6786a0bc8c9',
    'intercom-session-al0g0fgs': '',
    'intercom-device-id-al0g0fgs': 'e13363dc-7515-424f-ae47-32e50ef692b7',
    }

    headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    # 'Cookie': 'PHPSESSID=08jmanir8f6fki7t0ka9b16n16; intercom-id-al0g0fgs=fe6386ee-28f8-4392-a9bd-f6786a0bc8c9; intercom-session-al0g0fgs=; intercom-device-id-al0g0fgs=e13363dc-7515-424f-ae47-32e50ef692b7',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
    }
    
    response = requests.get(
        'https://misshosting.se/domainschecker.php?q=available&domain=' + domain,
        cookies=cookies,
        headers=headers,
    )

    json_response = response.json()
    
    
    #print(json_response['response'][0]['status'])
    
    return json_response['response'][0]['status']
    
    """
    #https://misshosting.se/domainschecker.php?q=available&domain=taken.se
    #https://misshosting.se/domainschecker.php?q=available&domain=taken.se
    
    domain_parts = tldextract.extract(url)

    if (domain_parts.suffix == ""):
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False    


    domain = domain_parts.domain + "." + domain_parts.suffix
    
    DOMAIN_API = "https://api.godaddy.com/v1/domains/available?domain="
    API_KEY = "h1JgSaN2VmpJ_TTiof91Kw8iqsSz67S8kRq"
    API_SECRET = "W9MoHC9NakTKG4ZdQJkLV1"  
    request_url = DOMAIN_API + domain

    response = requests.get(request_url, headers = {
            "Authorization": "sso-key " + API_KEY + ":" + API_SECRET
        })

    json_response = response.json()
    
    return json_response
    """

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
    #print(DNS_RECORDS.NOSTATUS.value)
    
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
                #return False
                return DNS_RECORDS.NOERROR
            
            if (response["status"] == "NXDOMAIN"):
                # We can assume the domain is available
                #return True
                return DNS_RECORDS.NXDOMAIN
            
            if (response["status"] == "SERVFAIL"):
                # We got a SERVFAIL, could not determine if domain is available
                #return False
                return DNS_RECORDS.SERVFAIL
        else:
            # Print an error message if the command failed
            print(result.stderr)
            raise Exception("Command failed with return code:", result.returncode)
        # print exit code
    except Exception as e:
        raise e

def isValidUrl(url):
    domain_parts = tldextract.extract(url)

    
    
    #client.get_domain(client, 'www.google.com')
    
    # Denna e lite skum
    # https://plus => domain_parts.domain är tom medan domain_parts.suffix == plus
    # Behöver därmed kolla båda
    
    # Disallowed suffixes to prevent false positives
    # E.x, adense. google returns NXDOMAIN as it is not used but it is not allowed to be purchased for obvious reasons
    disallowedSuffixes = ["google"]
    
    
    # Filter our invalid urls, e.x https://www.ads or https://a
    # Filter out invalid / disallowed suffixes
    # This is horrendus but it works
    if domain_parts.domain == "www" or domain_parts.suffix in disallowedSuffixes or domain_parts.suffix == "" or domain_parts.domain == "":
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False
    
    #print("Valid domain: " + str(url))
    return True

# If domain is available, return True
def domain_analysis(url):
    
    #doubleCheck(url)


    ## Very early test, promising but need to check if we can use it.
    
    try:
        response = requests.get("https://rdap.org/domain/svt.se")
    except Exception as e:
        print(e)
        
    print(response)
    
    #json_response = response.json()
    
    #expiration = json_response["events"]
    #expiration = expiration["expiration"]
    
    #print(json_response)
    #print(expiration)
    
    #print()
    #print(json_response["Events"])
    
    
    # If domain is full URL, extract domain
    
    #print(url)
    
    if isValidUrl(url) == False:
        return False, "false", DNS_RECORDS.INVALID
    
    domain_parts = tldextract.extract(url)
    
    

    """"     
    if (domain_parts.suffix == "" or domain_parts.domain == ""):
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False, "false", DNS_RECORDS.INVALID
    """

    domain = domain_parts.domain + "." + domain_parts.suffix
    

    ## domaindb needs to update their stuff...
    ## Here we assume the domain is taken, hence the NOERROR dns record set, maybe look into later on, I really don't know
    
    if domain_parts.suffix == "to" or domain_parts == "ly":
        return False, "false", DNS_RECORDS.NOERROR

    if domain in globals.checked_domains:
        return False, "false", DNS_RECORDS.NOERROR

    ## You can write like this but god will punish you and you will suffer in hell for all eternity
    # return not dns_nxdomain(domain)

    try:
        dns_reply = dns_nxdomain(domain)
        # dns query returned something

        if dns_reply == DNS_RECORDS.NXDOMAIN:
            return True, "dns", dns_reply
        else:
            return False, "dns", dns_reply
    except Exception as e:
        raise e

    # If we get here, we could not determine if the domain is available with DNS query   
    
    
    
    with globals.checked_domains_lock:
        globals.checked_domains.add(domain)
    try:
        if domain_parts.suffix.upper() in globals.GODADDY_TLDS:
            return godaddy_is_available(domain), "godaddy", dns_reply
        elif domain_parts.suffix.upper() in globals.DOMAINSDB_TLDS:
            return domainsdb_is_available(domain), "domaindb", dns_reply
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
