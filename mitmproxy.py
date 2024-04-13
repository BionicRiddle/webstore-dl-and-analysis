import socket
import ssl
import threading

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

def MITM_t(port):

    if port == None:
        raise Exception("Port is required")
        
    # Set up the listening socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(('127.0.0.1', port))
    listen_socket.listen(5)

    # Init list of some sort ??
    magic_object = {}

    while True:
        client_socket, addr = listen_socket.accept()
        print("Received connection from:", addr)
        client_handler = threading.Thread(target=handle_client, args=(client_socket,magic_object,))
        client_handler.start()

def MITM(num_clients):

    for i in range(num_clients):
        port = globals.MITM_PROXY_START_PORT + i
        client = threading.Thread(target=MITM_t, args=(port,))
        client.start()

if __name__ == "__main__":


    MITM(22300)
