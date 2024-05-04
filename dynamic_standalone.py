# This file is cursed. It is a standalone file that is used to run dynamic analysis on an extension.
import os
import time
import sqlite3

from dynamic import dynamic_analysis

class Extension:
    def __init__(self, crx_path: str) -> None:
        try: 
            self.creation_time = time.time()
            self.crx_path = crx_path
            self.id = crx_path.split('/')[-2]
            self.version = ".".join(crx_path.split('.')[0].split('_')[-4:])
      
            self.dynamic_analysis = []
        except Exception as e:
            reason = "Error in 'Extension.__init__'"
            failed_extension(crx_path, reason, e)
            raise Exception("Failed to create Extension object")

    def set_dynamic_analysis(self, dynamic_analysis) -> None:
        self.dynamic_analysis = dynamic_analysis
    
    def get_crx_path(self) -> str:
        return self.crx_path

    def get_version(self) -> str:
        return self.version
    
    def get_dynamic_analysis(self) -> dict:
        return self.dynamic_analysis

    def get_id(self) -> str:
        return self.id

    def age(self) -> float:
        return time.time() - self.creation_time
    
    def __str__(self) -> str:
        return self.crx_path

# CREATE TABLE domain_meta (domain TEXT NOT NULL, status TEXT, expired DATETIME, available DATETIME, remove DATETIME, raw_json TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (timestamp,domain))

# CREATE TABLE domain (domain TEXT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, filepath TEXT NOT NULL, PRIMARY KEY (domain,extension,version,filepath))

# CREATE TABLE dynamic (url TEXT NOT NULL, method TEXT NOT NULL, time_after_start FLOAT NOT NULL, extension TEXT NOT NULL, version TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (url, method, extension, version))

# load DB thesis.db
conn = sqlite3.connect('thesis.db')
c = conn.cursor()

extension_paths = []

# load list of NXDOMAIN domains
c.execute("SELECT DISTINCT d.extension FROM domain d JOIN domain_meta dm ON d.domain = dm.domain WHERE dm.status = 'NXDOMAIN' ORDER BY d.extension")

extension_ids = c.fetchall()

root_path = "./extensions/"

for extension_id in extension_ids[0]:
    extension_path = root_path + extension_id
    for crx in os.listdir(extension_path):
        if crx.endswith(".crx"):
            extension_paths.append(extension_path + '/' + crx)

print(extension_paths)

for extension_path in extension_paths:
    extension = Extension(extension_path)
    dynamic_analysis(extension)

    # Save
    dynamic_analysis = extension.get_dynamic_analysis()
    for entry in dynamic_analysis:
        c.execute("INSERT INTO dynamic (url, method, time_after_start, extension, version) VALUES (?,?,?,?,?)", (entry['url'], entry['method'], entry['time_after_start'], extension.get_id(), extension.get_version()))

