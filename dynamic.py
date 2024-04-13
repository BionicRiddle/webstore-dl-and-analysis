from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time
import psutil

def is_display_running(port):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if f":{port}" in " ".join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def none():
    chrome_options = webdriver.ChromeOptions()

    EXTENSION_PATH = '/mnt/c/Users/riddle/Documents/webstore-dl-and-analysis/extensions/hdokiejnpimakedhajhdlcegeplioahd/HDOKIEJNPIMAKEDHAJHDLCEGEPLIOAHD_4_125_0_4.crx' # LastPass

    PROXY_HOST = "http://127.0.0.1"
    PROXY_PORT = 8080

    # Check if there is a display on :99
    DISPLAY_PORT = 99
    if not is_display_running(DISPLAY_PORT):
        print(f"No display is running on port :{DISPLAY_PORT}. Starting a display on port :{DISPLAY_PORT}.")
        # Start a display on port :99
        os.system(f"Xvfb :{DISPLAY_PORT} -ac &> /dev/null &")

    # set DISPLAY variable to avoid crash
    os.environ['DISPLAY'] = f":{DISPLAY_PORT}"

    PROXY = PROXY_HOST + ":" + str(PROXY_PORT)

    chrome_options.add_extension(EXTENSION_PATH) 
    chrome_options.add_argument('--proxy-server=' + PROXY)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=640,480")


    driver = webdriver.Chrome(options=chrome_options)

    try: 
        driver.get("chrome://extensions/")
        #driver.get("https://albinkarlsson.se/")

        time.sleep(60)

    except KeyboardInterrupt:
        driver.close()
    driver.close()    

def dynamic_analysis(thread, extension):

    EXTENSION_PATH = extension.get_crx_path()

    PROXY_HOST = "http://127.0.0.1"
    PROXY_PORT = globals.MITM_PROXY_START_PORT + thread.get_thread_id()

    PROXY = PROXY_HOST + ":" + str(PROXY_PORT)

    # Check if proxy started???
    #...

    chrome_options.add_extension(EXTENSION_PATH) 
    chrome_options.add_argument('--proxy-server=' + PROXY)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=640,480")

    driver = webdriver.Chrome(options=chrome_options)

    # TEST START
    # Prepare proxy

    try:
        driver.get("chrome://extensions/")
        time.sleep(60)

    except e as Exception:
        print(e)
        driver.close()
        raise e

    driver.close()

    # TEST END
    # get proxy data

    

    return True


if __name__ == "__main__":
    pass