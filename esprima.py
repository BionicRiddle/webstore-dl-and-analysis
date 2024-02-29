import subprocess
import os
from colorama import Fore, Back, Style
import json

# Global variables and settings
import globals
#from helpers import *

class Esprima:
    def __init__(self, thread_id, args=None):
        node_script_args = [globals.NODE_PATH, globals.NODE_APP_PATH, thread_id]
        if args:
            node_script_args = args
        self._buffer_size = 500000
        self._pipe_to_node      = '/tmp/pipe_to_node_' + str(thread_id)
        self._pipe_from_node    = '/tmp/pipe_from_node_' + str(thread_id)

        # Remove the pipes if they already exist
        try:
            os.unlink(pipe_to_node)
        except:
            pass
        try:
            os.unlink(pipe_from_node)
        except:
            pass

        # Create named pipes
        os.mkfifo(self._pipe_to_node)
        os.mkfifo(self._pipe_from_node)

        # Open the pipes
        self._pipe_to_node_fd   = os.open(self._pipe_to_node,   os.O_WRONLY)
        self._pipe_from_node_fd = os.open(self._pipe_from_node, os.O_RDONLY)

        # Start the Node.js script as a subprocess
        self.node_process = subprocess.Popen(node_script_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def get_tokens(self, input_text):
        try:
            os.write(self._pipe_to_node_fd, input_text.encode()) # TODO: kolla om encode behövs
            return_string =  os.read(self._pipe_from_node_fd, self._buffer_size).decode()

            # if return_string begins with "Error: ", print it in red
            if return_string.startswith("Error: "):
                error = return_string.split("Error: ")[1]
                raise Exception(error)
            return return_string
        except Exception as e:
            self.close_process()

    def close_process(self):
        # Close the subprocess
        self.node_process.terminate()
        
        try:
            os.close(pipe_from_node_fd)
            os.close(pipe_to_node_fd)
        except:
            pass
        
        # Remove pipes
        try:
            os.unlink(self._pipe_to_node)
        except:
            pass
        try:
            os.unlink(self._pipe_from_node)
        except:
            pass

if __name__ == "__main__":
    # path like /www/EXTENSION_DIR
    input_dir = "node/app.js"

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
