from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os

# Set path to chrome/chromedriver as per your configuration
root_dir = os.path.dirname(os.path.abspath(__file__))
chromedriver_path = os.path.join(root_dir, "chromedriver/chromedriver-linux64/chromedriver")
chrome_path = os.path.join(root_dir, "chromedriver/chrome-linux64/chrome")



# --enable-features=ConversionMeasurement,AttributionReportingCrossAppWeb

# Setup chrome options
options = webdriver.ChromeOptions()
options.binary_location = chrome_path
options.add_argument("--headless") # Ensure GUI is off
#options.add_argument("--no-sandbox")
#options.add_argument('--proxy-server=127.0.0.1:8080')
#options.add_argument('--allow-running-insecure-content')
#options.add_argument('--ignore-certificate-errors')
#options.add_extension('/mnt/c/Users/Riddle/Documents/webstore-dl-and-analysis/extensions/fngmehpgladkgnmkinabkikbmhjmkigj/FNGMEHPGLADKGNMKINABKIKBMHJMKIGJ_1_0_0_0.crx')

webdriver_service = Service(chromedriver_path)

print("Launching Browser")
# Choose Chrome Browser
browser = webdriver.Chrome(service=webdriver_service, options=options)
#browser = webdriver.Chrome(service=webdriver_service, options=options)
print("Browser launched")

#driver.get("chrome://extensions/")
browser.get("https://riddle.nu/")












