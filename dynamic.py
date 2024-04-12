from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time

try: 
    chrome_options = webdriver.ChromeOptions()

    EXTENSION_PATH = '/mnt/c/Users/riddle/Documents/webstore-dl-and-analysis/extensions/hdokiejnpimakedhajhdlcegeplioahd/HDOKIEJNPIMAKEDHAJHDLCEGEPLIOAHD_4_125_0_4.crx' # LastPass

    PROXY_HOST = "http://127.0.0.1"
    PROXY_PORT = 8080

    PROXY = PROXY_HOST + ":" + str(PROXY_PORT)

    chrome_options.add_extension(EXTENSION_PATH) 
    chrome_options.add_argument('--proxy-server=' + PROXY)
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
        #chrome_options.add_argument('--headless')
        #chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=640,480")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get("chrome://extensions/")
    #driver.get("https://albinkarlsson.se/")

    time.sleep(60)

except KeyboardInterrupt:
    driver.close()
driver.close()
