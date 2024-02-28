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

pipe_from_node_fd = None

try:

    while True:
        os.mkfifo(pipe_to_node)
        os.mkfifo(pipe_from_node)

        input("Press Enter to continue...")

        print("pipes created")

        ## open the pipe
        pipe_to_node_fd = os.open(pipe_to_node, os.O_WRONLY)

        print("pipes created")

        # read file "input_file" and send it to the Node.js process
        input_file = "node/app.js"
        with open(input_file, 'r') as file:
            file_content = file.read().encode() + b'\n'
            if file_content == '':
                file_content = b'{}\n'
            os.write(pipe_to_node_fd, file_content)
        

        pipe_from_node_fd = os.open(pipe_from_node, os.O_RDONLY)
        print("waiting for the node to finish")

        ## read from the pipe
        print(os.read(pipe_from_node_fd, 100))

        print("done")

        remove_pipes()

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


