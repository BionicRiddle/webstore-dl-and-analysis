import signal
import subprocess
import sys
import time

import requests

# Global variables and settings
import globals


class Esprima:
    """Manage the Node.js Esprima server used for JavaScript parsing."""

    def __init__(self, host="localhost", port=12300):
        """Start the Node.js server and wait for it to become healthy."""
        self._debug_out = 'esprima_debug_out.txt'
        self._debug_handle = open(self._debug_out, 'a')

        self._host = host
        self._port = port

        node_script_args = [globals.NODE_PATH, globals.NODE_APP_PATH, str(self._host), str(self._port)]
        self._node_process = subprocess.Popen(node_script_args, stdout=self._debug_handle, stderr=subprocess.STDOUT)

        max_attempts = 100  # 10 seconds
        for _ in range(max_attempts):
            try:
                response = requests.get(f"http://{self._host}:{self._port}/health", timeout=1)
                if response.status_code == 200 and response.text == "OK":
                    break
            except Exception:
                pass
            time.sleep(0.1)
        else:
            self._node_process.terminate()
            try:
                self._node_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._node_process.kill()
            self._debug_handle.close()
            raise RuntimeError(
                f"Esprima Node.js server failed to start after {max_attempts * 0.1:.1f}s"
            )

    def run(self, method, input_text):
        """Send source text to the Esprima server and return the response body."""
        supported = ["tokenize", "parse"]
        if method not in supported:
            raise Exception("Method not supported. Supported methods: (" + ", ".join(supported) + ")")
        try:
            response = requests.post(
                "http://{}:{}/{}".format(self._host, self._port, method),
                data=input_text,
                headers={'Content-Type': 'text/plain'},
            )
            if response.status_code == 200:
                return response.text
            elif response.status_code == 418:  # Esprima error
                raise Exception("ESPRIMA: " + response.text)
            elif response.status_code == 400:
                return "{}"
            elif response.status_code == 413:
                raise Exception("413 Input too large: {:.4f} MB".format(len(input_text) / 1024 / 1024))
            else:  # Server error
                raise Exception("{} {}".format(response.status_code, response.text))
        except Exception as e:
            raise e

    def close_process(self):
        """Terminate the Node.js Esprima process gracefully."""
        if self._node_process.poll() is None:
            self._node_process.send_signal(signal.SIGINT)
            try:
                self._node_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._node_process.kill()
        if not self._debug_handle.closed:
            self._debug_handle.close()


if __name__ == "__main__":
    print("Run static_analysis.py instead to test Esprima.", file=sys.stderr)
