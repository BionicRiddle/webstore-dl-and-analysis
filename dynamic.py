from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time
import psutil
import json

# Global variables and settings
import globals
from helpers import *

def is_display_running(port):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if f":{port}" in " ".join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def dynamic_analysis(extension):

    EXTENSION_PATH = extension.get_crx_path()

    #TEMP
    # check if display is running on :99
    if not is_display_running(99):
        os.system("Xvfb :99 -ac &")
        os.environ['DISPLAY'] = ":99"
        print("Display started")

    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_extension(EXTENSION_PATH) 
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=640,480")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=chrome_options)

    # TEST START
    # Prepare proxy

    try:
        start_time = time.time()
        print("Start Time: ", start_time)
        
        driver.get("chrome://extensions/")
        #driver.get("https://albinkarlsson.se/")

        WAIT_TIME = 60

        chrome_logs = driver.get_log('performance')
        
        #time.sleep(5)
        time.sleep(60)

        # Filter logs for network entries
        network_logs = [chrome_log for chrome_log in chrome_logs if 'Network.requestWillBeSent' in chrome_log['message']]

        log = []

        # Print URLs accessed along with their methods
        for entry in network_logs:
               
            url     = ""
            method  = ""

            try:
                chrome_log = (json.loads(entry['message']))
                request = chrome_log['message']['params']['request']
                url = request['url']
                method = request['method']
                time_after_start = start_time - entry['timestamp']/1000

                # Filter favicon.ico
                if "/favicon.ico" in url:
                    continue

                # filter out data:image/png;base64
                if "data:image/png;base64" in url:
                    continue
                
                #filter if "chrome://" in beginning of url
                if "chrome://" == url[:9]:
                    continue

                log.append({
                    "url": url,
                    "method": method,
                    "time_after_start": time_after_start
                })

            except Exception as e:
                pass

    except Exception as e:
        print(e)
        driver.close()
        raise e

    driver.close()

    # Save
    extension.set_dynamic_analysis(log)

    return True


if __name__ == "__main__":
    dynamic_analysis = dynamic_analysis(1, None)
    print(dynamic_analysis)