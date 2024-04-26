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
from datetime import datetime


#Unoffcial API KEY (Samuel)
#Key: h1Jo22moy2n4_Wqi1sKQDBAzRYbPKDYuaoM
#Secret: QGRs57FnetX9qQsNVbXKeL

# curl -X 'GET' 'https://api.godaddy.com/v1/domains/available?domain=npms.io&checkType=FAST&forTransfer=true'  -H 'accept: application/json'   -H 'Authorization: sso-key h1Jo22moy2n4_Wqi1sKQDBAzRYbPKDYuaoM:QGRs57FnetX9qQsNVbXKeL'


GODADDY_TLDS = []

def godaddy_is_available(domain, max_retries=3):
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

def rdap(domain, max_retries=3):
    #print(Style.DIM + 'Checking domain %s with GoDaddy' % domain + Style.RESET_ALL)
    DOMAIN_API = "https://rdap.org/domain/"
    
    request_url = DOMAIN_API + domain

    RATE_PER_MINUTE = 5000 # 10000 får biland ratelimit

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url, headers = {})
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    raise Exception("Error in response")
            elif response.status_code == 400:
                raise Exception("Invalid request (malformed path, unsupported object type, invalid IP address, etc)")
            elif response.status_code == 403:
                print(f"(403) Blocked due to abuse or other misbehaviour? Retrying in 1 second (Attempt {attempt + 1}/{max_retries}) for {domain}")
                time.sleep(1)
            elif response.status_code == 404:
                return {"Status": "TLD_NOT_SUPPORTED_OR_DOMAIN_NOT_FOUND"}
            elif response.status_code == 429:
                print(f"(429) RDAP Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries}) for {domain}")
                time.sleep(1)
            elif response.status_code == 500:
                raise Exception("RDAP is broken")
            else:
                raise Exception("Unexpected code " + str(response.status_code))
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)
            
        # Test
        sleep((60 / RATE_PER_MINUTE) * globals.NUM_THREADS)

    raise Exception(f"Failed to get response after {max_retries} attempts")

def domainsdb_is_available(domain, max_retries=3):
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
                        print("djaskldjkasldjlkas")
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

def dns_analysis(domain: str):
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
                #print("NOERROR")
                # We got a response, no need to continue
                #return False
                return DNS_RECORDS.NOERROR
            
            if (response["status"] == "NXDOMAIN"):
                # We can assume the domain is available
                return DNS_RECORDS.NXDOMAIN
            
            if (response["status"] == "SERVFAIL"):
                # We got a SERVFAIL, could not determine if domain is available
                return DNS_RECORDS.SERVFAIL
        else:
            # Print an error message if the command failed
            print(result.stderr)
            raise Exception("Command failed with return code:", result.returncode)
        # print exit code
        
    except Exception as e:
        if (e.args[0] == 2):
            globals.TEMINATE = True
            print(Fore.RED + "ZDNS could not be found." + Style.RESET_ALL)
        raise e

# https://datatracker.ietf.org/doc/html/rfc8056
# Returns a bunch of stuff (i hate this)
def rdap_analysis(domain):
    try:
        ret = rdap(domain)

        if len(ret) == 0:
            return None, None, None, None
        
        rdap_dump = json.dumps(ret).replace("'", "''")
        expiration_date = None
        available_date = None
        deleted_date = None

        if ret and 'events' in ret:
            for event in ret['events']:
                if ('eventAction' in event and 'eventDate' in event):
                    if event['eventAction'] == 'expiration': 
                        expiration_date = datetime.fromisoformat(event['eventDate'])
                    if event['eventAction'] == 'auto renew period':
                        available_date = datetime.fromisoformat(event['eventDate'])
                    if event['eventAction'] == 'pending delete':
                        deleted_date = datetime.fromisoformat(event['eventDate'])
        return (rdap_dump, expiration_date, available_date, deleted_date)
    except Exception as e:
        raise Exception("RDAP analysis failed: " + str(e))

# If domain is available, return True
def domain_analysis(url):
    print(Fore.RED + "Deprecated" + Style.RESET_ALL)
        
    #json_response = response.json()
    
    #expiration = json_response["events"]
    #expiration = expiration["expiration"]
    
    #print(json_response)
    #print(expiration)
    
    #print()
    #print(json_response["Events"])
    
    
    # If domain is full URL, extract domain
    
    #print(url)
    
    domain_parts = tldextract.extract(url)

    """"     
    if (domain_parts.suffix == "" or domain_parts.domain == ""):
        #raise Exception("No suffix found for domain: %s" % domain_parts.domain)
        return False, "false", DNS_RECORDS.INVALID
    """

    domain = domain_parts.domain + "." + domain_parts.suffix

    # RDAP API

    if domain_parts.suffix in globals.RDAP_TLDS:
        try:
            ret = rdap(domain)

            for event in ret:
                print(event)

            if len(ret) != 0:
                print("Domain: " + domain)
                print()

            # # 2024-08-03T04:00:00Z
            # # check if less than 1 mont of now
            # expiration_time = datetime.datetime.fromisoformat(ret[:-1])
            # # print(Style.DIM + str(expiration_time) + Style.RESET_ALL)
            # if expiration_time < datetime.datetime.now() + datetime.timedelta(days=30):
            #     print(Style.BRIGHT + Fore.RED + "Domain is expiring soon: " + domain + Style.RESET_ALL)
            #     print(Style.BRIGHT + Fore.RED + "Expiration date: " + str(expiration_time) + Style.RESET_ALL)
            #     print(Style.BRIGHT + Fore.RED + "Time until expiration: " + str(expiration_time - datetime.datetime.now()) + Style.RESET_ALL)
            #     print()
                        
        except Exception as e:
            #print(e)
            pass
            
    else:
        return False, "false", DNS_RECORDS.NOERROR

    raise Exception("haha nothing")
    

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

    url_file = "found_domains.txt"

    # read file and parse json
    with open(url_file, 'r') as file:
        
        # split each line
        lines = file.read().split('\n')
    

        for full_domain in lines:
            try:
                suffix = tldextract.extract(full_domain).suffix
                if suffix == "io":
                    continue
                domain = tldextract.extract(full_domain).domain
                combined = domain + "." + suffix
                ret = rdap(combined)

                print(json.dumps(ret, indent=4))
                continue
                # 2024-08-03T04:00:00Z
                # check if less than 1 mont of now
                expiration_time = datetime.datetime.fromisoformat(ret[:-1])
                # print(Style.DIM + str(expiration_time) + Style.RESET_ALL)
                if expiration_time < datetime.datetime.now() + datetime.timedelta(days=30):
                    print(Style.BRIGHT + Fore.RED + "Domain is expiring soon: " + domain + Style.RESET_ALL)
                    print(Style.BRIGHT + Fore.RED + "Expiration date: " + str(expiration_time) + Style.RESET_ALL)
                    print(Style.BRIGHT + Fore.RED + "Time until expiration: " + str(expiration_time - datetime.datetime.now()) + Style.RESET_ALL)
                    print()
            except Exception as e:
                print(e)
