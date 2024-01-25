import subprocess
import json

class SubprocessHandler:
    def __init__(self, args):
        # Start the Node.js script as a subprocess
        self.node_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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

        return output_lines

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

# Define the command-line arguments for the Node.js script
node_script_args = ['node', 'app.js']

# Create an instance of the SubprocessHandler with the specified arguments
subprocess_handler = SubprocessHandler(node_script_args)

# Communicate with the Node.js process
while True:
    file_path = input("Enter file path (type 'exit' to quit): ")

    # Send the file path to the Node.js process
    subprocess_handler.send_input(file_path)

    if not file_path:
        continue

    # Check if the user wants to exit
    if file_path.lower() in ['exit', 'quit', 'q']:
        break

    # Read output from the Node.js process
    output_lines = subprocess_handler.read_output()

    try:
        # Parse the JSON output and print it pretty
        print(json.dumps(json.loads(''.join(output_lines)), indent=2))
    except json.JSONDecodeError:
        # Print the output as-is if it's not JSON
        print(''.join(output_lines))

# Close the subprocess
subprocess_handler.close_process()
