import subprocess
import json
import os

## köras när tråd startas
#node = SubprocessHandler(node_script_args)

## köras när tråd stängs
#node.close_process()

class SubprocessHandler:
    def __init__(self, args):
        # Environment variables for the Node.js script
        NODE_PATH = os.environ.get("NODE_PATH", "node")
        NODE_APP_PATH = os.environ.get("NODE_APP_PATH", './node/app.js')

        # Define the command-line arguments for the Node.js script
        node_script_args = [NODE_PATH, NODE_APP_PATH]
        
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

