import socket
import ssl
import threading
from enum import Enum

def handle_client(client_socket, magic_object):

    # Receive the client's request
    request = client_socket.recv(4096)
    print("Request:")
    print(request.decode())

    first_line = request.decode().split('\n')[0]
    method = first_line.split(' ')[0]

    # Check if it's a CONNECT request
    if method == "CONNECT":
        # Extract the host and port from the CONNECT request
        url = first_line.split(' ')[1]
        target_host, target_port = url.split(':')
        target_port = int(target_port)

        # Establish a connection to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))

        # Send a successful response to the client
        response = "HTTP/1.1 200 OK\n\n"
        client_socket.send(response.encode())

        # Start relaying data between the client and server
        relay(client_socket, target_socket)
    else:
        # Extract the host and port from the request
        url = first_line.split(' ')[1]
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        # log url

        with magic_object.pipe_list_lock:
            print(temp)
            magic_object.pipe_list.append(temp)

        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        # Create a socket to connect to the web server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((webserver, port))
        server_socket.send(request)

        # Start relaying data between the client and server
        relay(client_socket, server_socket)


def relay(socket1, socket2):
    while True:
        # Receive data from socket1 and send it to socket2
        data = socket1.recv(4096)
        if data:
            socket2.send(data)
        else:
            break

    # Close both sockets
    socket1.close()
    socket2.close()

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
        self.listen_socket.listen(5)

        self.pipe_list_lock = threading.Lock()
        self.pipe_list = []

        self.running = threading.Lock()

        self.state = MITM_STATE.IDLE
    
    def stop(self):
        self.active = False

    def start(self):
        self.active = True
        thread = threading.Thread(target=lambda: self._handle_connections())
        self.state = MITM_STATE.RUNNING
        thread.start()

    def _handle_connections(self):
        while True:
            client_socket, addr = self.listen_socket.accept()
            print("Received connection from:", addr)
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,self,))
            client_handler.start()
            if self.state == MITM_STATE.ENDING:
                break
        self.state = MITM_STATE.WAITING
    
    def end(self):
        self.active = False
        # Wait for the thread to finish
        with self.running:
            with self.pipe_list_lock:
                return_list = self.pipe_list


    def terminate(self):
        # Close the listening socket
        self.listen_socket.close()

if __name__ == "__main__":


    l = MITM_link(22300)

    l.start()

    # do stuff

    l.stop()
    l.get_pipe_list()