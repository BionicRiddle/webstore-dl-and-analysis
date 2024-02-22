import zipfile
from colorama import Fore, Back, Style
import json
import tempfile
import threading
import random
from keywords_search import analyze
from domain_analysis import domain_analysis
import os
import time
import shutil
import globals
from helpers import *
import json
import db

# Extension class

class Extension:
    def __init__(self, crx_path: str) -> None:
        try: 
            self.crx_path = crx_path
            self.manifest = read_manifest(crx_path)
            
            self.extracted_path = ""
            self.keyword_analysis = {
                "list_of_urls": [],
                "list_of_actions": [],
                "list_of_common_urls": []
            }
            self.static_analysis = {}
            self.dynamic_analysis = {}
            self.domain_analysis = {}
        except Exception as e:
            failed_extension(crx_path, str(e))
            raise Exception("Failed to create Extension object")

    def clean_up(self) -> None:
        if self.extracted_path:
            shutil.rmtree(self.extracted_path)
            #print(Fore.YELLOW + 'Cleaned up %s' % self.extracted_path + Style.RESET_ALL)
        else:
            ## wait for usier input
            #input("No extracted path to clean up, press enter to continue. %s" % self.crx_path)
            raise Exception("No extracted path to clean up")

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

    def get_extracted_files(self) -> list:
        pass
    
    def __str__(self) -> str:
        return self.crx_path

# File locks
unknown_file_ext_lock = threading.Lock()
failed_lock = threading.Lock()
failed_run_lock = threading.Lock()
domain_found_lock = threading.Lock()

FILE_EXTENSIONS_SKIP = ["JPG", "PNG", "ICO", "GIF", "SVG", "TTF", "WOFF", "WOFF2", "EOT", "MD", "DS_STORE"]
FILE_EXTENSIONS_TEXT = ["JS", "CSS", "HTML", "JSON", "TXT", "XML", "YML", "TS", "CFG", "CONF"]

def domain_found(domain: str) -> None:
    with domain_found_lock:
        with open('found_domains.txt', 'a') as f:
            f.write(domain + '\n')

def failed_extension(crx_path: str, reason: str = "") -> None:
    with failed_lock:
        with open('failed.txt', 'a') as f:
            f.write(crx_path + '\t' + reason + '\n')

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
            except:
                failed_extension(crx_path)
                return
            #print(Fore.GREEN + 'Extracted %s \t %s' % (tmp_path, crx_path) + Style.RESET_ALL)
            return tmp_path
    except Exception as e:
        failed_extension(crx_path, str(e))
        raise Exception("Failed to extract extension")

def read_manifest(crx_path: str) -> dict:
    try:
        # using zipfile, read data manifest.json
        # return json
        with zipfile.ZipFile(crx_path, 'r') as zip_ref:
            manifest = json.loads(zip_ref.read('manifest.json'))
            return manifest
    except Exception as e:
        failed_extension(crx_path , str(e))
        raise Exception("Failed to read manifest")
    
            

## ------------------------------

# This is the main function that is called from search.py
# It is called with a path to a crx file
# It shpuld not return anything, but write to files
# It may throw exceptions indicating that the extension could not be analyzed
def analyze_extension(extension_path: str, sql) -> None:
    # create obj Extension
    try:
        extension = Extension(extension_path)
    except Exception as e:
        failed_extension(extension_path, str(e))
        return

    manifest = extension.get_manifest()
        

    manifest_version = manifest['manifest_version']
    #print(Fore.GREEN + 'Manifest version: %s' % manifest_version)
    
    # of no permissions skip
    if 'permissions' not in manifest:
        pass
    
    # if no host permissions skip
    if 'host_permissions' not in manifest:
        pass
    
    # Extract file
    try:
        extension.set_extracted_path(extract_extension(extension_path))
    except Exception as e:
        #input("Failed to EXTRACT extension %s, press enter to continue" % extension_path)
        pass


    try:
        
        # --- Keyword search ---
        # keyword search, find all FILE_EXTENSIONS_TEXT in extracted files
        # if found, do keyword_analysis()
        if extension.get_extracted_path() is None:
            failed_extension(extension_path)
            return

        # --- Keyword analysis ---
        
        # Rename analyze
        analyze(extension, False, extension)

        urls = extension.get_keyword_analysis()['list_of_urls']
        actionsList = extension.get_keyword_analysis()['list_of_actions']
        commonUrls = extension.get_keyword_analysis()['list_of_common_urls']
        
        
        #with sql as c:
        db.create_table(sql)
        #db.insertDomainTable(c, urls)
        #db.insertActionTable(c, actionsList)
        db.insertUrlTable(sql, commonUrls)
        
        #c.execute("SELECT * FROM domain")
        #print(c.fetchone())
    # --- Static analysis ---1
            

        # --- Dynamic analysis ---

        # --- Write to file ---
        # write keyword search stuff to file
        # write static analysis stuff to file
        # write dynamic analysis stuff to file
    except Exception as e:
        # if any exception during analysis, do a clean up to prevent disk filling up
        extension.clean_up()
        raise

    # --- Clean up ---
    extension.clean_up()

    # do domain analysis

    urls = extension.get_keyword_analysis()['list_of_urls']

    for s_url in list(urls):
        for url in s_url:
            if len(url) == 0:
                return

            try:
                if (domain_analysis(url)):
                    print(Fore.GREEN + 'Domain %s is available' % url + Style.RESET_ALL)
                    domain_found(url)
            except Exception as e:
                failed_extension(extension_path, str(e))
                continue

if __name__ == "__main__":
    raise Exception("This file is not meant to be run directly")
