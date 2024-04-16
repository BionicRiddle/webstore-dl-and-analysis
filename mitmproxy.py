# NOT USED

import socket
import ssl
import threading
from enum import Enum
import time

def relay(socket1, socket2):
    while True:
        # Receive data from socket1 and send it to socket2
        data = socket1.recv(4096)
        print(len(data))
        if data:
            socket2.send(data)
        else:
            break

    # Close both sockets
    print("Closing sockets")
    socket1.close()
    print("Closed Client socket")
    socket2.close()
    print("Closed Server socket")

class MITM_STATE(Enum):
    IDLE = 0
    RUNNING = 1
    ENDING = 2
    WAITING = 3


class MITM_link:
    '''
    Class to handle the MITM proxy and communication with the proxy
    '''

    def __init__(self, port):
        self.active = False
        self.port = port

        # Start the MITM proxy
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind(('127.0.0.1', port))
        self.listen_socket.listen(10)
        
        self.pipe_list_lock = threading.Lock()
        self.pipe_list = []

        self.running = threading.Lock()

        self.state = MITM_STATE.IDLE

    def start(self):
        self.active = True
        thread = threading.Thread(target=lambda: self._handle_connections())
        self.state = MITM_STATE.RUNNING
        thread.start()

    def _handle_connections(self):
        while True:
            client_socket, addr = self.listen_socket.accept()
            print("Received connection from:", addr)
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()
            if self.state == MITM_STATE.ENDING:
                break
        self.state = MITM_STATE.WAITING
    
    def end(self) -> list:
        self.state = MITM_STATE.ENDING
        # Wait for the thread to finish
        with self.running:
            with self.pipe_list_lock: # should not be needed
                return_list = self.pipe_list
                self.pipe_list = []
                return return_list

    def terminate(self):
        # Close the listening socket
        self.listen_socket.close()

    def handle_client(self, client_socket):
        request = client_socket.recv(4096).decode('utf-8')
        print(request)
        first_line = request.split('\n')[0]
        url = first_line.split(' ')[1]

        host = url.split(':')[0]
        port = int(url.split(':')[1])

        # add to pipe list
        with self.pipe_list_lock:
            print("Adding to pipe list")
            self.pipe_list.append(host)


        print(f"Received request for: {host}")

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((host, port))
        ssl_socket = ssl.wrap_socket(remote_socket)

        ssl_socket.sendall(request.encode())

        while True:
            data = ssl_socket.recv(4096)
            if len(data) > 0:
                client_socket.send(data)
            else:
                break

        ssl_socket.close()
        client_socket.close()

if __name__ == "__main__":
    # NOT USED

    try:


        l = MITM_link(22300)

        l.start()
        print("Started")

        # do stuff
        time.sleep(60)

        output = l.end()

        print(output)

    
    except KeyboardInterrupt:

        output = l.end()

        print(len(output))
        print(output)

        print("Terminating...")
        l.terminate()
        print("Exiting...")