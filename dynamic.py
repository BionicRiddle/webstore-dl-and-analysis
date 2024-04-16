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

def dynamic_analysis(thread, extension):

    #EXTENSION_PATH = extension.get_crx_path()

    # Check if proxy started???
    #...

    chrome_options = webdriver.ChromeOptions()

    #chrome_options.add_extension(EXTENSION_PATH) 
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=640,480")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=chrome_options)

    # TEST START
    # Prepare proxy

    try:
        #driver.get("chrome://extensions/")
        driver.get("https://albinkarlsson.se/picture.webp")
        logs = driver.get_log('performance')
        time.sleep(5)
        # driver.get("https://gp.se/")
        # time.sleep(5)
        # driver.get("https://google.se/")
        # time.sleep(5)
        # driver.get("https://www.svt.se/")
        # time.sleep(5)
        # driver.get("https://www.aftonbladet.se/")
        # time.sleep(5)
        # driver.get("https://www.expressen.se/")
        # time.sleep(5)
        # driver.get("https://www.svd.se/")
        # time.sleep(5)
        # driver.get("https://www.di.se/")
        # time.sleep(5)
        # driver.get("https://www.dn.se/")
        # time.sleep(5)
        # driver.get("https://www.metro.se/")
        # time.sleep(5)
        # driver.get("https://www.hd.se/")
        # time.sleep(5)
        # driver.get("https://www.sydsvenskan.se/")
        # time.sleep(5)
        #time.sleep(60)

        # Filter logs for network entries
        network_logs = [log for log in logs if 'Network.requestWillBeSent' in log['message']]

        # Print URLs accessed along with their methods
        for entry in network_logs:
            try:
                level = entry['level']
                log = (json.loads(entry['message']))
                url = log['message']['params']['request']['url']
                print(url)
                #method = message['method']
                #print(f"URL: {url}, Method: {method}")
            except Exception as e:
                print(e)
                pass

        # for each line in logs:
        # remove file if exists
        if os.path.exists("log.txt"):
            os.remove("log.txt")

        for log in logs:
            json_s = log.get("message")
            with open("log.txt", "a") as f:
                f.write(json_s + "\n")


    except Exception as e:
        print(e)
        driver.close()
        raise e

    driver.close()

    # TEST END
    # get proxy data

    

    return True


if __name__ == "__main__":
    dynamic_analysis = dynamic_analysis(1, None)
    print(dynamic_analysis)