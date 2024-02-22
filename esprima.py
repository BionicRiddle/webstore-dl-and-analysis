import subprocess
import os
from colorama import Fore, Back, Style

# Global variables and settings
import globals
#from helpers import *

class Esprima:
    def __init__(self, args=None):
        node_script_args = [globals.NODE_PATH, globals.NODE_APP_PATH]
        if args:
            node_script_args = args
        # Start the Node.js script as a subprocess
        self.node_process = subprocess.Popen(node_script_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def send_input(self, input_text):
        # Send input to the Node.js process
        self.node_process.stdin.write(input_text + '\n')
        self.node_process.stdin.flush()

    def read_output(self):
        # Read all available lines from stdout and stderr
        output_lines = []
        while True:
            # Read from both stdout and stderr
            line_stdout = self.node_process.stdout.readline().strip()

            # Break if both streams are empty
            if not line_stdout:
                break

            # Append output from stdout
            output_lines.append(line_stdout)
        
        return ''.join(output_lines)

    def read_error(self):
        # Read all available lines from stderr
        error_lines = []
        while True:
            # Read from stderr
            line_stderr = self.node_process.stderr.readline().strip()

            # Break if stderr is empty
            if not line_stderr:
                break

            # Append output from stderr
            error_lines.append(line_stderr)

        return error_lines

    def close_process(self):
        # Close the subprocess
        self.node_process.stdin.close()
        self.node_process.stdout.close()
        self.node_process.stderr.close()
        self.node_process.wait()


if __name__ == "__main__":
    # path like /www/EXTENSION_DIR
    input_dir = "./"

    # Environment variables for the Node.js script

    # Define the command-line arguments for the Node.js script


    # Create an instance of the Esprima with the specified arguments
    subprocess_handler = Esprima()


    # for esch file in input_dir, reciursively

    for file in os.listdir(input_dir):
        if file.endswith(".js"):
            print(os.path.join(input_dir, file))
            subprocess_handler.send_input(os.path.join(input_dir, file))

            # Read the output from the Node.js process
            output_lines = subprocess_handler.read_output()

            # convert output to json
            json_output = json.loads(output_lines)

            # pretty print the output

            print(json.dumps(json_output, indent=2))

    # Close the subprocess
    subprocess_handler.close_process()
