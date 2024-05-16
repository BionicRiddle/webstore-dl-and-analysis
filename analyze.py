import zipfile
from colorama import Fore, Back, Style
import json
import tempfile
import threading
import random
from keywords_search import analyze
from domain_analysis import dns_analysis, rdap_analysis
from static_analysis import static_analysis
from dynamic import dynamic_analysis
from manifest import manifest_analysis
import os
import time
import shutil
import globals
from globals import DNS_RECORDS
from helpers import *
import json
import db
import traceback

# Extension class

class Extension:
    def __init__(self, crx_path: str) -> None:
        try: 
            self.creation_time = time.time()
            self.crx_path = crx_path
            self.manifest = read_manifest(crx_path)
            self.id = crx_path.split('/')[-2]
            self.version = ".".join(crx_path.split('.')[0].split('_')[-4:])
            
            self.extracted_path = ""
            self.keyword_analysis = {
                "list_of_urls": None,
                "list_of_actions": None,
                "list_of_common_urls": None
            }
            self.static_analysis = {}
            self.dynamic_analysis = []
            self.domain_analysis = {}
        except Exception as e:
            reason = "Error in 'Extension.__init__'"
            failed_extension(crx_path, reason, e)
            raise Exception("Failed to create Extension object")

    def clean_up(self) -> None:
        """
        Cleans up the extracted files by removing the directory specified in `self.extracted_path`.

        This method is typically called after the analysis of the extension is complete and the extracted files are no longer needed.

        """

        # Safety checks to prevent accidental deletion of important files
        if not self.extracted_path:
            failed_extension(self.crx_path, "No extracted path to clean up", e)
            return

        if not os.path.exists(self.extracted_path):
            raise Exception("Extracted path does not exist")

        if not os.path.isdir(self.extracted_path):
            failed_extension(self.crx_path, "Extracted path is not a directory", e)
            return

        if not self.extracted_path.startswith('/tmp/'):
            raise Exception("Extracted path is not in /tmp/")

        if len(self.extracted_path) < 6:
            raise Exception("Something definitely went wrong! Extracted path is too short")

        if ".." in self.extracted_path:
            raise Exception("Something definitely went wrong! Extracted path contains '..'")

        # Remove the extracted files
        try:
            shutil.rmtree(self.extracted_path)
        except Exception as e:
            failed_extension(self.crx_path, "Failed to clean up extracted files", e)
            return

    def set_extracted_path(self, extracted_path: str) -> None:
        self.extracted_path = extracted_path

    def set_keyword_analysis(self, keyword_analysis) -> None:
        self.keyword_analysis = keyword_analysis
    
    def set_static_analysis(self, static_analysis) -> None:
        self.static_analysis = static_analysis
    
    def set_dynamic_analysis(self, dynamic_analysis) -> None:
        self.dynamic_analysis = dynamic_analysis
    
    def get_crx_path(self) -> str:
        return self.crx_path

    def get_version(self) -> str:
        return self.version
    
    def get_manifest(self) -> dict:
        return self.manifest
    
    def get_extracted_path(self) -> str:
        #print(self.extracted_path)
        return self.extracted_path

    def get_keyword_analysis(self) -> dict:
        return self.keyword_analysis
    
    def get_static_analysis(self) -> dict:
        return self.static_analysis
    
    def get_dynamic_analysis(self) -> dict:
        return self.dynamic_analysis

    def get_extracted_files(self) -> list:
        pass

    def get_id(self) -> str:
        return self.id

    def age(self) -> float:
        return time.time() - self.creation_time
    
    def __str__(self) -> str:
        return self.crx_path

# File locks
unknown_file_ext_lock = threading.Lock()
failed_lock = threading.Lock()
failed_run_lock = threading.Lock()
domain_found_lock = threading.Lock()
time_lock = threading.Lock()

FILE_EXTENSIONS_SKIP = ["JPG", "PNG", "ICO", "GIF", "SVG", "TTF", "WOFF", "WOFF2", "EOT", "MD", "DS_STORE"]
FILE_EXTENSIONS_TEXT = ["JS", "CSS", "HTML", "JSON", "TXT", "XML", "YML", "TS", "CFG", "CONF"]

def domain_found_godaddy(domain: str) -> None:
    with domain_found_lock:
        with open('found_domains_godaddy.txt', 'a') as f:
            f.write(domain + '\n')
            
def domain_found_misshosting(domain: str) -> None:
    with domain_found_lock:
        with open('found_domains_misshosting.txt', 'a') as f:
            f.write(domain + '\n')

def failed_extension(crx_path: str, reason: str = "", exception=None) -> None:
    """
    Logs the failure of a process on a given extension into "failed.txt".

    This function is thread-safe and can be used concurrently from multiple threads.

    Args:
        crx_path (str): The path of the extension that failed.
        reason (str, optional): The reason for the failure. Defaults to an empty string.
        exception (Exception, optional): The exception that was raised, if any. Defaults to None.

    Usage:
        If an extension fails to process for any reason, you can log the failure like this:

        >   try:
        >       # Code to process the extension
        >       do_stuff_that_might_fail_with_an_exception(crx_path)
        >   except Exception as e:
        >       # If an exception is raised, log the failure and the exception
        >       failed_extension(crx_path, "Processing failed", e)

        If you know the reason for the failure but no exception was raised, you can log the failure like this:
        
        >   if not is_valid_extension(crx_path):
        >       # If the extension is not valid, log the failure
        >       failed_extension(crx_path, "Invalid extension")
    """
    with failed_lock:
        with open('failed.txt', 'a') as f:
            e = ""
            if exception:
                e = "\tWith Exception: [" + str(exception) + "]"
            path = crx_path.split('/')[-1]
            f.write(path + ':\t' + reason + e + '\n')
            f.write(traceback.format_exc() + '\n\n')

# TODO: Dynamic analysis stuff
def failed_run(crx_path: str) -> None:
    with failed_run_lock:
        #TODO: write to file
        print('Failed to run extension %s' % crx_path)

def unknown_file_extension(crx_paths: list) -> None:
    with unknown_file_ext_lock:
        with open('unknown-ext.txt', 'a') as f:
            for crx_path in crx_paths:
                ext = crx_path.split('.')[-1] if '.' in crx_path else 'NO_EXT'
                out = '%s\t%s' % (ext, crx_path)
                f.write(out + '\n')

def extract_extension(crx_path: str) -> str:
    try: 
        # using zipfile, extract to tmp dir
        # return path to tmp dir
        with zipfile.ZipFile(crx_path, 'r') as zip_ref:
            tmp_path = tempfile.mkdtemp()
            try:
                zip_ref.extractall(tmp_path)
            except Exception as e:
                failed_extension(crx_path, "Failed to extract extension", e)
                return
            return tmp_path
    except Exception as e:
        failed_extension(crx_path, "Failed to extract extension", e)
        raise Exception("Failed to extract extension")

def read_manifest(crx_path: str) -> dict:
    try:
        # using zipfile, read data manifest.json
        # return json
        with zipfile.ZipFile(crx_path, 'r') as zip_ref:
            manifest = json.loads(zip_ref.read('manifest.json'))
            return manifest
    except Exception as e:
        failed_extension(crx_path, "Failed to read manifest", e)
        raise Exception("Failed to read manifest")
    
            

## ------------------------------

# This is the main function that is called from search.py
# It is called with a path to a crx file
# It shpuld not return anything, but write to files
# It may throw exceptions indicating that the extension could not be analyzed
def analyze_extension(thread, extension_path: str) -> None:
    globals.extension_counter = globals.extension_counter + 1

    # print if globals.extension_counter is divisible by 500 to see progress
    if globals.extension_counter % 500 == 0:
        print(globals.extension_counter)

    start_time = time.time()

    # create obj Extension
    try:
        extension = Extension(extension_path)

        # Extract file
        extension.set_extracted_path(extract_extension(extension_path))

        # --- Keyword search ---
        # keyword search, find all FILE_EXTENSIONS_TEXT in extracted files
        # if found, do keyword_analysis()
        if extension.get_extracted_path() is None:
            failed_extension(extension_path, "Extension was not extracted properly")
            return True
    except Exception as e:
        # if any exception during analysis, do a clean up to prevent disk filling up
        try:
            extension.clean_up()
        except:
            print(Fore.RED + 'Failed to clean up after failed extension: %s' % extension_path + Style.RESET_ALL)
            pass
        #Log to file
        failed_extension(extension_path, "Something went wrong with the file or filesystem", e)
        return True

    # Save time
    extraction_time = time.time() - start_time

    try:
        # --- Read Manifest ---

        manifest_urls = manifest_analysis(extension.get_manifest())

        manifest_time = time.time() - start_time

        # --- Keyword analysis ---
        
        # Rename analyze
        analyze(extension, False, extension)

        urls = extension.get_keyword_analysis()['list_of_urls']

        actionsList = extension.get_keyword_analysis()['list_of_actions']
        #commonUrls = extension.get_keyword_analysis()['list_of_common_urls']

        for url in manifest_urls:
            path = extension.get_id() + "/manifest.json"
            if url in urls:
                if path not in urls[url]:
                    urls[url].append(path)
            else:
                urls[url] = [path]

        keyword_time = time.time() - start_time

        # --- Static analysis ---
           
        if globals.STATIC_ENABLE:
            static_analysis(extension, thread.esprima)

        static_time = time.time() - start_time

        # --- Dynamic analysis ---

        if globals.DYNAMIC_ENABLE:
            dynamic_analysis(extension)
            print(extension.get_dynamic_analysis())

        dynamic_time = time.time() - start_time

        # --- Write to file ---
        # write keyword search stuff to file
        # write static analysis stuff to file
        # write dynamic analysis stuff to file
    except Exception as e:
        # if any exception during analysis, do a clean up to prevent disk filling up
        extension.clean_up()
        #Log to file
        failed_extension(extension_path, "Something went wrong when analyzing the extension source code", e)
        return True

    # --- Clean up ---
    extension.clean_up()

    cleanup_time = time.time() - start_time

    invalidUrls = []

    for url, files in urls.items():
        
            
        if globals.TEMINATE:
            # Will return False to indicate that the thread was terminated before finishing
            return False
        if len(url) == 0:
            print(Fore.RED + 'Possible error: Empty URL' + Style.RESET_ALL)
            continue
        try:
            # domain:   example.com
            # tld:      com
            domain, tld = get_valid_domain(url)
            dns_status = None
                    
            #print("Url: " + str(url))
            #print("Domain: " + str(domain))
            #print("_________________")

            # Check if domain is valid
            if domain == None or tld == None:
                # If invalid, remove from url list - Debate on wheter we should do this
                invalidUrls.append(url)
                dns_status = DNS_RECORDS.INVALID
                #print(Fore.RED + 'Invalid URL:  %s' % url + Style.RESET_ALL)
            else:
                # Check if domain already tested during current run
                do_dns = True
                with globals.checked_domains_lock:
                    if domain in globals.checked_domains:
                        do_dns = False
                    globals.checked_domains.add(domain)
                if do_dns:

                    results = dns_analysis(domain)


                    dns_status = results.value
                    
                        
                    globals.dns_records[domain] = dns_status
                    
                    rdap_dump = None
                    expiration_date = None
                    available_date = None
                    deleted_date = None

                    rdap_results = None
                    if (globals.RDAP_ENABLE):
                        if (results == globals.DNS_RECORDS.NXDOMAIN):
                            # i hate this
                            if tld in globals.RDAP_TLDS:
                                rdap_dump, expiration_date, available_date, deleted_date = rdap_analysis(domain)
                            else:
                                # If RDAP is not supported by TLD
                                rdap_dump = '{"STATUS": "RDAP_NOT_SUPPORTED"}'
                    # We only want this to run if we just did dns (and rdap)
                    db.insertDomainMetaTable(extension, thread.sql, domain, dns_status, expiration_date, available_date, deleted_date, rdap_dump)
                # We always want to do this even if we skipped dns
                # We want a rectord for each file the url is in
                for file in files:
                    file_whitout_id = file.split("/", 1)[1]
                    
                    db.insertDomainTable(extension, thread.sql, domain, extension_path, file_whitout_id)
        except Exception as e:
            failed_extension(extension_path, "Failed to analyze domain", e)
            continue

    dns_time = time.time() - start_time

    # DB Stuff

    
    #print(globals.dns_records)
    #print(invalidUrls)

    for action in actionsList:
        for domain in list(actionsList[action]):
            if domain in invalidUrls or domain not in urls:
                #print(domain)
                del actionsList[action][domain]
            
    #print(url_dns_record["github.com"])    

    db.insertActionTable(extension, thread.sql, actionsList, globals.dns_records)
    #db.insertUrlTable(thread.sql, commonUrls, url_dns_record)

    if globals.DYNAMIC_ENABLE:
        db.insertDynamicTable(extension, thread.sql, extension.get_dynamic_analysis())

    db_time = time.time() - start_time

    # --- Write time to time file ---
    with time_lock:
        with open('time.txt', 'a') as f:
            fromated = '''Extension: %s
            Start time: %s
            Extraction time: %s
            Manifest time: %s
            Keyword time: %s
            Static time: %s
            Dynamic time: %s
            Cleanup time: %s
            DNS time: %s
            DB time: %s\n''' % (extension_path, start_time, extraction_time, manifest_time, keyword_time, static_time, dynamic_time, cleanup_time, dns_time, db_time)
            f.write(fromated)

    return True
    
    

if __name__ == "__main__":
    raise Exception("This file is not meant to be run directly")
