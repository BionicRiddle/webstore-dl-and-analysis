import os
import time
import random
from time import sleep
import requests

start_time = time.time()

javascript_code = """
function addNumbers(a, b) {
    return a + b;)
}
"""

count = 0

NUM = 0
PORT = 12300 + NUM

node_server_url = "http://localhost:" + str(PORT)

pipe_to_node = '/tmp/pipe_to_node_' + str(NUM)
pipe_from_node = '/tmp/pipe_from_node_' + str(NUM)

while True:
    count += 1
    try: 
        # Make a POST request to the Node.js server
        url = node_server_url + "/parse"
        response = requests.post(url, data="test", headers={'Content-Type': 'text/plain'})

        # Check the response status and content
        if response.status_code == 200:
            #print(response.text)
            pass
        else:
            print('Esprima processing failed with status code', response.status_code)
            print('Server response:', response.text)

    except KeyboardInterrupt:
        break


print("Total time: ", time.time() - start_time)
print("Total count: ", count)
print("Ext per second: ", count / (time.time() - start_time))


