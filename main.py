import time
import os
import datetime
import requests
import json
import random
from queue import Queue
from threading import Thread



# Based on https://bitbucket.org/chalmerslbs/extensions_chrome/src/d789f8b3e71c667c540541098f5790f7a7fc3cf6/scraper/chrome/scraper_chrome.py#lines-114
def download_id(ext_id, repo, old_version=None):
    # print("[+] Extension id: ", ext_id)
    # dl_url = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=63.0&x=id%3D" + ext_id + "%26installsource%3Dondemand%26uc"
    dl_url = 'https://clients2.google.com/service/update2/crx?response=redirect&os=linux&arch=x86-64&os_arch=x86-64&nacl_arch=x86-64&prod=chromiumcrx&prodchannel=unknown&prodversion=52.0.2743.116&acceptformat=crx2,crx3&x=id%3D'+ext_id+'%26uc'
    print("[+] CRX url: ", dl_url)
    tries = 5
    r = None
    while tries > 0:
        time.sleep(1 + random.random())
        tries = tries - 1
        try:
            print(tries)
            r = requests.get(dl_url)
            break
        except Exception as e:
            open("failed-dls.txt", "a+").write(dl_url + "\n")
            print(tries, ": Failed, ", dl_url , " E: ", e)
            # wait_time = 10 + random.random() * 10 + random.random() * 10 * (5-tries)
            wait_time = 120
            print("Waiting, ", wait_time)
            time.sleep(wait_time)

    if not r:
        open("failed-dls.txt", "a+").write(dl_url + "\tNONE-RESPONSE\n")
        return None
    if r.status_code != 200:
        open("failed-dls.txt", "a+").write(dl_url + "\tNON-200-CODE\n")
        return None


    print("Final CRX URL: ", r.url)
    extension_crx_name_and_version = r.url.split("/")[-1]
    # GCHLFAHFCDODHNEMPCKAHOANMMAFLHKL_10_0_0_0.crx

    print("Name and version: ", extension_crx_name_and_version)

    if extension_crx_name_and_version == old_version:
        print("Got the version, skipping...")
        return extension_crx_name_and_version

    # Create dir
    if not os.path.isdir(repo+ext_id):
        os.makedirs(repo+ext_id)

    with open(repo+ext_id+"/"+extension_crx_name_and_version, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    return extension_crx_name_and_version



def get_database(path):
    database = {}
    if not os.path.isfile(path):
        open(path, "w+").write("")
    for line in open(path, "r"):
        try: 
            entry = json.loads(line)
        except:
            print("JSON FAILED!")
            print(line)
        # This will overwrite older versions, we just care about newest

        # However, make sure we don't overwrite a version with null.
        # This can happend due to a bug.

        database[entry["id"]] = entry

    return database

def add_entry_database(path, entry):
    open(path, "a+").write(json.dumps(entry) + "\n")

# date=None will be today
def get_sitemap(date=None):
    now = datetime.datetime.now()
    dir_name = now.strftime('%Y-%m-%d')
    dir_path = f'data_sitemaps/{dir_name}'
    print("dir_path, ", dir_path)
    files = os.listdir(dir_path)
    for f in files:
        if f.startswith("sitemap"):
            return dir_path + "/" + f


# Using pablo's sitemap doesnt currently work since it trims out lastmod
# def get_sitemap(date=None):
#     now = datetime.datetime.now()
#     date_str = now.strftime('%Y%m%d')
#     sitemap_path = f'/home/pablop/Documents/devel/WebStoreCrawl/sitemap/data/extensions_{date_str}.json'
#     return sitemap_path
 
 


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()


def handle_sitemap_line(sitemap_line):
    (url, lastmod) = sitemap_line.split("\t")
    eid = url.split("/")[-1]


    print("Download ", eid, "from", url)
    last_version = None
    if eid in database:
        last_version = database[eid]["version"]
    version = download_id(eid, extension_repo, last_version)
    entry = {"id": eid, "version": version, "sitemap": sitemap_file, "lastmod": lastmod, "now": str(datetime.datetime.now())}
    if not version:
        entry["version"] = "ERROR"
        print("Failed to download eid")
        open("fails.txt", "a+").write("Failed to download " + eid + "\n")

    add_entry_database(version_database, entry)


version_database = "version_database.txt"
# sitemap_file = get_sitemap()
sitemap_file = "data_sitemaps/sitemap_2024-01-17_021301.tsv"
extension_repo = "extensions/"
database = get_database(version_database)



# Used to ignore lines from the sitemap for themes/apps, the file is updated daily 
# with the sitemap
extension_ids = set(open("data_sitemaps/extensions.txt").read().split("\n"))

new_sitemap_lines = []
for sitemap_line in open(sitemap_file):
    if not sitemap_line:
        continue

    sitemap_line = sitemap_line[:-1] # remove \n

    (url, lastmod) = sitemap_line.split("\t")
    eid = url.split("/")[-1]
    if not eid in extension_ids:
        continue


    if eid in database:
        # 1 - Compare the time we downloaded it with the new lastmod
        d1 =  datetime.datetime.fromisoformat(database[eid]["now"])
        d2 =  datetime.datetime.fromisoformat(lastmod)
        lastmodDiff = (d2-d1.replace(tzinfo=datetime.timezone.utc)).total_seconds()
        # print(eid, lastmodDiff, sep="\t")
        if lastmodDiff > 0:
            new_sitemap_lines.append( sitemap_line )
    else:
        # print("is ", eid, "new?")
        new_sitemap_lines.append( sitemap_line )



now = datetime.datetime.now()
open("run-log.txt", "a+").write( str(now) +  ", Using sitemap: " + str(sitemap_file) + "\t" + "Downloading " + str(len(new_sitemap_lines)) + " total extensions\n")


# print("DEBUG")
# for sitemap_line in new_sitemap_lines:
#     print("Run for 1 line")
#     handle_sitemap_line(sitemap_line)
#     print("Done Run for 1 line")
# print("/DEBUG")
#

pool = ThreadPool(int(os.getenv("THREADS", 1)))
pool.map(handle_sitemap_line, new_sitemap_lines)
pool.wait_completion()
