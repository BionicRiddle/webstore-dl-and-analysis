import zipfile
from colorama import Fore, Back, Style
import json
import tempfile
import threading
import random
#from keywords_search import keyword_analysis_file
import os
import time

# Extension class

class Extension:
    def __init__(self, crx_path):
        self.crx_path = crx_path
        self.manifest = read_manifest(crx_path)
        self.extracted_path = ""
        self.static_analysis = {}
        self.dynamic_analysis = {}
        self.domain_analysis = {}

    def set_extracted_path(self, extracted_path):
        self.extracted_path = extracted_path
    
    def set_static_analysis(self, static_analysis):
        self.static_analysis = static_analysis
    
    def set_dynamic_analysis(self, dynamic_analysis):
        self.dynamic_analysis = dynamic_analysis

    def set_domain_analysis(self, domain_analysis):
        self.domain_analysis = domain_analysis
    
    def get_crx_path(self):
        return self.crx_path
    
    def get_manifest(self):
        return self.manifest
    
    def get_extracted_path(self):
        return self.extracted_path
    
    def get_static_analysis(self):
        return self.static_analysis
    
    def get_dynamic_analysis(self):
        return self.dynamic_analysis
    
    def get_domain_analysis(self):
        return self.domain_analysis
    
    def __str__(self):
        return self.crx_path

# File locks
unknown_file_ext_lock = threading.Lock()
failed_lock = threading.Lock()
failed_run_lock = threading.Lock()

FILE_EXTENSIONS_SKIP = ["JPG", "PNG", "ICO", "GIF", "SVG", "TTF", "WOFF", "WOFF2", "EOT", "MD", "DS_STORE"]
FILE_EXTENSIONS_TEXT = ["JS", "CSS", "HTML", "JSON", "TXT", "XML", "YML", "TS", "CFG", "CONF"]

def failed_extension(crx_path, reason=""):
    with failed_lock:
        with open('failed.txt', 'a') as f:
            f.write(crx_path + '\t' + reason + '\n')

# TODO: Dynamic analysis stuff
def failed_run(crx_path):
    with failed_run_lock:
        #TODO: write to file
        print('Failed to run extension %s' % crx_path)

def unknown_file_extension(crx_paths):
    with unknown_file_ext_lock:
        with open('unknown-ext.txt', 'a') as f:
            for crx_path in crx_paths:
                ext = crx_path.split('.')[-1] if '.' in crx_path else 'NO_EXT'
                out = '%s\t%s' % (ext, crx_path)
                f.write(out + '\n')

def extract_extension(self, crx_path):
    # using zipfile, extract to tmp dir
    # return path to tmp dir
    with zipfile.ZipFile(crx_path, 'r') as zip_ref:
        tmp_path = tempfile.mkdtemp()
        try:
            zip_ref.extractall(tmp_path)
        except:
            failed_extension(crx_path)
            return
        return tmp_path

def read_manifest(crx_path):
    # using zipfile, read data manifest.json
    # return json
    with zipfile.ZipFile(crx_path, 'r') as zip_ref:
        try:
            manifest = json.loads(zip_ref.read('manifest.json'))
        except:
            failed_extension(crx_path)
            return
        return manifest

## ------------------------------

# Main function
def analyze_extension(extension_path):
    # create obj Extension
    extension = Extension(extension_path)

    manifest = extension.get_manifest()

    manifest_version = manifest['manifest_version']
    print(Fore.GREEN + 'Manifest version: %s' % manifest_version)

    # of no permissions skip
    if 'permissions' not in manifest:
        pass
    
    # if no host permissions skip
    if 'host_permissions' not in manifest:
        pass
    
    # Extract file
    extension.set_extracted_path(extract_extension(extension_path))

    # keyword search, find all FILE_EXTENSIONS_TEXT in extracted files
    # if found, do keyword_analysis()
    if extension.get_extracted_path() is None:
        failed_extension(extension_path)
        return
    else:
        # do keyword analysis
        for root, dirs, files in os.walk(extension.get_extracted_path()):
            for file in files:
                if file.split('.')[-1] in FILE_EXTENSIONS_TEXT:
                    print('Analyzing file %s' % os.path.join(root, file))
                    return
                    keyword_analysis_file(os.path.join(root, file))

    # static analysis

    # dynamic analysis

    # write results to file

    # cleanup

    # do domain analysis


if __name__ == "__main__":
    raise Exception("This file is not meant to be run directly")