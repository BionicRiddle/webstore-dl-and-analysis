from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time
import psutil
import json
import requests


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
    """Run the extension in Chrome and collect network requests from performance logs."""
    EXTENSION_PATH = extension.get_crx_path()

    driver = None
    session = None

    # Check if running in docker
    if globals.IN_DOCKER:

        # Specify the URL of the Selenium Grid server
        grid_url = 'http://selenium-hub:4444/wd/hub'

        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_extension(EXTENSION_PATH) 
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
            #chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=640,480")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        chrome_options.set_capability("browserVersion", "124.0");
        chrome_options.set_capability("browserName", "chrome");

        driver = webdriver.Remote(command_executor=grid_url, options=chrome_options)
        session = driver.session_id
        #print("Session ID: ", session)
    
    else:
        # check if display is running on the configured display port
        if not is_display_running(globals.DISPLAY_PORT):
            # Xvfb is launched as a background process; errors are silently ignored
            os.system(f"Xvfb :{globals.DISPLAY_PORT} -ac &")
            print("Display started")
        os.environ['DISPLAY'] = f":{globals.DISPLAY_PORT}"

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
        
        driver.get("chrome://extensions/")
        #driver.get("https://albinkarlsson.se/")

        time.sleep(globals.DYNAMIC_WAIT_TIME)
        chrome_logs = driver.get_log('performance')

        # Filter logs for network entries
        network_logs = [chrome_log for chrome_log in chrome_logs if 'Network.requestWillBeSent' in chrome_log['message']]

        log = []

        # Print URLs accessed along with their methods
        for entry in network_logs:
               
            url     = ""
            method  = ""

            try:
                chrome_log = json.loads(entry['message'])
                request = chrome_log['message']['params']['request']
                url = request['url']
                method = request['method']
                time_after_start = entry['timestamp'] / 1000 - start_time

                # Filter favicon.ico
                if "/favicon.ico" in url:
                    continue

                # filter out data:image/png;base64
                if "data:image" == url[:10]:
                    continue
                
                #filter if "chrome://" in beginning of url
                if "chrome://" == url[:9]:
                    continue
                
                if "chrome-extension://" == url[:19]:
                    continue

                log.append({
                    "url": url,
                    "method": method,
                    "time_after_start": time_after_start
                })

            except (KeyError, json.JSONDecodeError) as e:
                print(f"Warning: failed to parse Chrome log entry: {e}")

    except Exception as e:
        print(e)
        driver.close()
        if globals.IN_DOCKER:
            requests.delete(f"http://selenium-hub:4444/session/{session}")
        raise e

    driver.close()
    if globals.IN_DOCKER:
        requests.delete(f"http://selenium-hub:4444/session/{session}")

    # Save
    extension.set_dynamic_analysis(log)

    return True


if __name__ == "__main__":
    raise RuntimeError("Run dynamic_standalone.py to run dynamic analysis.")