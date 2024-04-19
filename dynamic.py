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

    #TEMP
    # check if display is running on :99
    if not is_display_running(99):
        os.system("Xvfb :99 -ac &")
        os.environ['DISPLAY'] = ":99"
        print("Display started")

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

        with open("log2.txt", "w") as f:
            s = ""
            for entry in network_logs:
                s = s + str(entry) + "\n\n"
            f.write(s)

        # Print URLs accessed along with their methods
        for entry in network_logs:
               
            url     = ""
            method  = ""

            try:
                log = (json.loads(entry['message']))
                request = log['message']['params']['request']
                url = request['url']
                method = request['method']

                # Filter favicon.ico
                if "/favicon.ico" in url:
                    print("Skip")
                    print(url)
                    continue

                output = method + " " + url
                with open("log.txt", "w") as f:
                    f.write(output + "\n" + str(entry) + "\n")

            except Exception as e:
                pass

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