import os
import time
import random
from time import sleep

start_time = time.time()

NUM = 0
BUFFER_SIZE = 500000

pipe_to_node = '/tmp/pipe_to_node_' + str(NUM)
pipe_from_node = '/tmp/pipe_from_node_' + str(NUM)

def remove_pipes():
    try:
        os.unlink(pipe_to_node)
    except:
        pass

    try:
        os.unlink(pipe_from_node)
    except:
        pass

## remove the pipes if they already exist
try:
    os.unlink(pipe_to_node)
    print("Existing pipe_to_node removed")
except:
    pass
try:
    os.unlink(pipe_from_node)
    print("Existing pipe_from_node removed")
except:
    pass

## Open and read files into list
strgs = []
input_files = ["node/script.js"]
for input_file in input_files:
    with open(input_file, 'r') as file:
        file_content = file.read().encode()
        strgs.append(file_content)
        
count = 0

## create named pipes

pipe_from_node_fd = None

try:
    os.mkfifo(pipe_to_node)
    os.mkfifo(pipe_from_node)

    ## open the pipe
    pipe_to_node_fd = os.open(pipe_to_node, os.O_WRONLY)
    pipe_from_node_fd = os.open(pipe_from_node, os.O_RDONLY)

    while True:

        input("Press Enter to continue...")

        # read file "input_file" and send it to the Node.js process
        os.write(pipe_to_node_fd, random.choice(strgs))
        
        #print("waiting for the node to finish")

        ## read from the pipe
        return_string = os.read(pipe_from_node_fd, BUFFER_SIZE).decode()

        print(return_string)

        count += 1

        # send null
        #os.write(pipe_to_node_fd, b'\0')
        #sleep(1)

except Exception as e:
    remove_pipes()
    raise
except KeyboardInterrupt as e:
    try:
        os.close(pipe_from_node_fd)
        os.close(pipe_to_node_fd)
        print("closed!")
    except:
        print("pipe_from_node_fd already closed")
        pass
    remove_pipes()

print("Total time: ", time.time() - start_time)
print("Total count: ", count)
print("Ext per second: ", count / (time.time() - start_time))


