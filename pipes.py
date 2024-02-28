import os
import time

NUM = 0

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
    os.unlink(pipe_from_node)
    print("Existing pipes removed")
except:
    pass

## create named pipes

try:

    while True:
        os.mkfifo(pipe_to_node)
        os.mkfifo(pipe_from_node)

        ## open the pipes
        pipe_to_node_fd = os.open(pipe_to_node, os.O_WRONLY)
        pipe_from_node_fd = os.open(pipe_from_node, os.O_RDONLY)

        # read file "input_file" and send it to the Node.js process
        input_file = "node/app.js"
        with open(input_file, 'r') as file:
            file_content = file.read().encode() + b'\n'
            if file_content == '':
                file_content = b'{}\n'
            os.write(pipe_to_node_fd, file_content)
        os.close(pipe_to_node_fd)

        ## read from the pipe
        print(os.read(pipe_from_node_fd, 100))
        os.close(pipe_from_node_fd)

        remove_pipes()

except Exception as e:
    remove_pipes()
    raise
except KeyboardInterrupt as e:
    remove_pipes()


