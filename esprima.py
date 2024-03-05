import subprocess
import requests
import time

# Global variables and settings
import globals
#from helpers import *

class Esprima:
    def __init__(self, host="localhost", port=12300):
        self._debug_out = 'esprima_debug_out.txt'

        self._host = host
        self._port = port

        node_script_args = [globals.NODE_PATH, globals.NODE_APP_PATH, str(self._host), str(self._port)]
        self._node_process = subprocess.Popen(node_script_args, stdout=open(self._debug_out, 'a'), stderr=subprocess.STDOUT)
        
        while True:
            try:
                response = requests.get("http://" + self._host + ":" + str(self._port) + "/health")
                if response.status_code == 200:
                    if response.text == "OK":
                        break
            except:
                time.sleep(0.1)

    def run(self, method, input_text):
        suported = ["tokenize", "parse"]
        if method not in suported:
            raise Exception("Method not supported. Supported methods: (" + ", ".join(suported) + ")")
        try:
            response = requests.post("http://{}:{}/{}".format(self._host, self._port, method), data=input_text, headers={'Content-Type': 'text/plain'})
            if response.status_code == 200:
                return response.text
            elif response.status_code == 418: # Esprima error
                raise Exception("ESPRIMA: " + response.text)
            elif response.status_code == 400:
                return "{}"
            elif response.status_code == 413:
                # print size of input_text in MB
                raise Exception("413 Input too large: {:.4f} MB".format(len(input_text) / 1024 / 1024))
            else: # Server error
                raise Exception("{} {}".format(response.status_code, response.text))
        except Exception as e:
            raise e
    def close_process(self):
        # Close the subprocess
        self._node_process.send_signal(2)

if __name__ == "__main__":

    print("Öhh, outdated")
    sys.exit(1)
    
    from colorama import Fore, Back, Style
    import json

    # path like /www/EXTENSION_DIR
    input_dir = "node/test.js"

    # Environment variables for the Node.js script

    # Define the command-line arguments for the Node.js script


    # Create an instance of the Esprima with the specified arguments
    subprocess_handler = Esprima()

    # read file "input_dir" and send it to the Node.js process
    with open(input_dir, 'r') as file:
        subprocess_handler.send_input(file.read())

    # Read the output from the Node.js process
    output_lines = subprocess_handler.read_output()

    print(Fore.GREEN + "Output from Node.js script:" + Style.RESET_ALL)
    print(output_lines)

    # convert output to json
    json_output = json.loads(output_lines)

    # pretty print the output

    print(json.dumps(json_output, indent=2))

    # Close the subprocess
    subprocess_handler.close_process()
