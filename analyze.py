"""Per-extension orchestration for the Chrome extension analysis pipeline.

This module extracts an extension, runs manifest, keyword, static, dynamic,
and DNS/RDAP analysis, then persists the collected results to the database and
log files.
"""

import zipfile
from colorama import Fore, Back, Style
import json
import tempfile
import threading
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
import db
import traceback

# File output and extension handling configuration
FAILED_LOG_FILE = "failed.txt"
UNKNOWN_EXT_LOG_FILE = "unknown-ext.txt"
TIMING_LOG_FILE = "time.txt"

FILE_EXTENSIONS_SKIP = ["JPG", "PNG", "ICO", "GIF", "SVG", "TTF", "WOFF", "WOFF2", "EOT", "MD", "DS_STORE"]
FILE_EXTENSIONS_TEXT = ["JS", "CSS", "HTML", "JSON", "TXT", "XML", "YML", "TS", "CFG", "CONF"]  # Keep in sync with keywords_search.py's file type list.

# File locks
unknown_file_ext_lock = threading.Lock()
failed_lock = threading.Lock()
time_lock = threading.Lock()


class Extension:
    """Represents one extension version while it moves through the analysis pipeline."""

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
            failed_extension(self.crx_path, "No extracted path to clean up")
            return

        if not os.path.exists(self.extracted_path):
            raise Exception("Extracted path does not exist")

        if not os.path.isdir(self.extracted_path):
            failed_extension(self.crx_path, "Extracted path is not a directory")
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
        return self.extracted_path

    def get_keyword_analysis(self) -> dict:
        return self.keyword_analysis
    
    def get_static_analysis(self) -> dict:
        return self.static_analysis
    
    def get_dynamic_analysis(self) -> dict:
        return self.dynamic_analysis

    def get_id(self) -> str:
        return self.id

    def age(self) -> float:
        return time.time() - self.creation_time
    
    def __str__(self) -> str:
        return self.crx_path

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
        with open(FAILED_LOG_FILE, 'a') as f:
            e = ""
            if exception:
                e = "\tWith Exception: [" + str(exception) + "]"
            path = crx_path.split('/')[-1]
            f.write(path + ':\t' + reason + e + '\n')
            f.write(traceback.format_exc() + '\n\n')

def unknown_file_extension(crx_paths: list) -> None:
    with unknown_file_ext_lock:
        with open(UNKNOWN_EXT_LOG_FILE, 'a') as f:
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

def analyze_extension(thread, extension_path: str) -> None:
    """Run the per-extension pipeline: extract, manifest, keyword, static, dynamic, DNS/RDAP, then persist results to the database."""
    with globals.extension_counter_lock:
        globals.extension_counter += 1
        extension_count = globals.extension_counter

    if extension_count % 500 == 0:
        print(extension_count)

    start_time = time.time()
    extension = None

    try:
        extension = Extension(extension_path)
        extension.set_extracted_path(extract_extension(extension_path))

        if extension.get_extracted_path() is None:
            failed_extension(extension_path, "Extension was not extracted properly")
            return True
    except Exception as e:
        try:
            if extension is not None:
                extension.clean_up()
        except Exception:
            print(Fore.RED + 'Failed to clean up after failed extension: %s' % extension_path + Style.RESET_ALL)
        failed_extension(extension_path, "Something went wrong with the file or filesystem", e)
        return True

    extraction_time = time.time() - start_time

    try:
        manifest_urls = manifest_analysis(extension.get_manifest())
        manifest_time = time.time() - start_time

        analyze(extension, False, extension)

        urls = extension.get_keyword_analysis()['list_of_urls']
        actionsList = extension.get_keyword_analysis()['list_of_actions']

        for url in manifest_urls:
            path = extension.get_id() + "/manifest.json"
            if url in urls:
                if path not in urls[url]:
                    urls[url].append(path)
            else:
                urls[url] = [path]

        keyword_time = time.time() - start_time

        if globals.STATIC_ENABLE:
            static_analysis(extension, thread.esprima)

        static_time = time.time() - start_time

        if globals.DYNAMIC_ENABLE:
            dynamic_analysis(extension)
            print(extension.get_dynamic_analysis())

        dynamic_time = time.time() - start_time
    except Exception as e:
        try:
            extension.clean_up()
        except Exception:
            print(Fore.RED + 'Failed to clean up after failed extension: %s' % extension_path + Style.RESET_ALL)
        failed_extension(extension_path, "Something went wrong when analyzing the extension source code", e)
        return True

    extension.clean_up()
    cleanup_time = time.time() - start_time

    invalidUrls = []

    for url, files in urls.items():
        if globals.TERMINATE:
            return False
        if len(url) == 0:
            print(Fore.RED + 'Possible error: Empty URL' + Style.RESET_ALL)
            continue
        try:
            domain, tld = get_valid_domain(url)
            dns_status = None

            if domain is None or tld is None:
                invalidUrls.append(url)
                dns_status = DNS_RECORDS.INVALID
            else:
                if globals.DNS_ENABLE:
                    do_dns = True
                    with globals.checked_domains_lock:
                        if domain in globals.checked_domains:
                            do_dns = False
                        globals.checked_domains.add(domain)

                    if do_dns:
                        dns_status = dns_analysis(domain)

                        with globals.dns_records_lock:
                            globals.dns_records[domain] = dns_status

                        rdap_dump = None
                        expiration_date = None
                        available_date = None
                        deleted_date = None

                        if globals.RDAP_ENABLE and dns_status == globals.DNS_RECORDS.NXDOMAIN:
                            if tld in globals.RDAP_TLDS:
                                rdap_dump, expiration_date, available_date, deleted_date = rdap_analysis(domain)
                            else:
                                rdap_dump = '{"STATUS": "RDAP_NOT_SUPPORTED"}'

                        db.insertDomainMetaTable(
                            extension,
                            thread.sql,
                            domain,
                            dns_status.value,
                            expiration_date,
                            available_date,
                            deleted_date,
                            rdap_dump,
                        )

                for file in files:
                    file_whitout_id = file.split("/", 1)[1]
                    db.insertDomainTable(extension, thread.sql, domain, extension_path, file_whitout_id)
        except Exception as e:
            failed_extension(extension_path, "Failed to analyze domain", e)
            continue

    dns_time = time.time() - start_time

    for action in actionsList:
        for domain in list(actionsList[action]):
            if domain in invalidUrls or domain not in urls:
                del actionsList[action][domain]

    with globals.dns_records_lock:
        dns_records = dict(globals.dns_records)
    db.insertActionTable(extension, thread.sql, actionsList, dns_records)

    if globals.DYNAMIC_ENABLE:
        db.insertDynamicTable(extension, thread.sql, extension.get_dynamic_analysis())

    db_time = time.time() - start_time

    with time_lock:
        with open(TIMING_LOG_FILE, 'a') as f:
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
