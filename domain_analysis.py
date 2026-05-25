"""Helpers for domain availability checks using GoDaddy, RDAP, DomainsDB, and zdns."""

from colorama import Fore, Style
import os
import subprocess
import requests
import time
import json
from time import sleep
import globals
from globals import DNS_RECORDS
from datetime import datetime

GODADDY_API_ENDPOINT = os.getenv("GODADDY_API_ENDPOINT", "https://api.godaddy.com/v1/domains/available?domain=")
GODADDY_API_KEY = os.getenv("GODADDY_API_KEY", "")
GODADDY_API_SECRET = os.getenv("GODADDY_API_SECRET", "")
RDAP_API_ENDPOINT = os.getenv("RDAP_API_ENDPOINT", "https://rdap.org/domain/")
DOMAINSDB_API_ENDPOINT = os.getenv("DOMAINSDB_API_ENDPOINT", "https://api.domainsdb.info/v1/domains/search?domain=")

# Conservative per-minute limit used to pace concurrent GoDaddy requests.
GODADDY_RATE_LIMIT_PER_MIN = 60
# Conservative limit; 10000/min sometimes triggers rate limiting.
RDAP_RATE_LIMIT_PER_MIN = 5000


def godaddy_is_available(domain, max_retries=3):
    """Check domain availability using the GoDaddy availability API."""
    request_url = GODADDY_API_ENDPOINT + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(
                request_url,
                headers={
                    "Authorization": "sso-key " + GODADDY_API_KEY + ":" + GODADDY_API_SECRET
                },
            )

            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "available" in json_response:
                        return json_response["available"]
                    raise Exception("Missing available key in response")
                except ValueError:
                    raise Exception("Error in response")
            elif response.status_code == 429:
                print(f"GoDaddy Rate limit exceeded. Retrying in 1 second (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            elif response.status_code == 422:
                return False
            else:
                print(f"Unexpected code {response.status_code}. Retrying (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
        except requests.RequestException as e:
            print(f"Request failed with exception: {e}. Retrying (Attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

        sleep((60 / GODADDY_RATE_LIMIT_PER_MIN) * int(globals.NUM_THREADS))

    raise Exception(f"Failed to get response after {max_retries} attempts")


def rdap(domain, max_retries=3):
    """Fetch RDAP data for a domain from the configured RDAP endpoint."""
    request_url = RDAP_API_ENDPOINT + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url, headers={})

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

        sleep((60 / RDAP_RATE_LIMIT_PER_MIN) * int(globals.NUM_THREADS))

    raise Exception(f"Failed to get response after {max_retries} attempts")


def domainsdb_is_available(domain, max_retries=3):
    """Check domain availability using the DomainsDB API."""
    request_url = DOMAINSDB_API_ENDPOINT + domain

    for attempt in range(max_retries):
        try:
            response = requests.get(request_url)
            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "domains" in json_response:
                        return False, "None"
                    raise Exception(f"Unexpected DomainsDB response: {json_response}")
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


def dns_analysis(domain: str):
    """Resolve a domain with the local zdns binary and map the status to DNS_RECORDS."""
    record_type = "NS"
    try:
        # Uses the bundled zdns binary at ./zdns/zdns. The command reads a domain from
        # stdin and writes a single JSON object to stdout with a top-level "status" field.
        command = ["./zdns/zdns", record_type, "--verbosity", "1"]
        result = subprocess.run(command, input=domain, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            response = json.loads(result.stdout)

            if "status" not in response:
                raise Exception("Go command failed: " + result.stdout)

            if response["status"] == "NOERROR":
                return DNS_RECORDS.NOERROR

            if response["status"] == "NXDOMAIN":
                return DNS_RECORDS.NXDOMAIN

            if response["status"] == "SERVFAIL":
                return DNS_RECORDS.SERVFAIL
        else:
            print(result.stderr)
            raise Exception(f"zdns command failed with return code: {result.returncode}")
    except FileNotFoundError:
        globals.TERMINATE = True
        print(Fore.RED + "zdns binary not found at ./zdns/zdns" + Style.RESET_ALL)
        raise
    except Exception as e:
        raise


# https://datatracker.ietf.org/doc/html/rfc8056
def rdap_analysis(domain):
    """Extract the RDAP payload and key lifecycle dates for a domain."""
    try:
        ret = rdap(domain)

        if len(ret) == 0:
            return None, None, None, None

        rdap_dump = json.dumps(ret)
        expiration_date = None
        available_date = None
        deleted_date = None

        if ret and "events" in ret:
            for event in ret["events"]:
                if "eventAction" in event and "eventDate" in event:
                    if event["eventAction"] == "expiration":
                        expiration_date = datetime.fromisoformat(event["eventDate"])
                    if event["eventAction"] == "auto renew period":
                        available_date = datetime.fromisoformat(event["eventDate"])
                    if event["eventAction"] == "pending delete":
                        deleted_date = datetime.fromisoformat(event["eventDate"])
        return (rdap_dump, expiration_date, available_date, deleted_date)
    except Exception as e:
        raise Exception("RDAP analysis failed: " + str(e))
