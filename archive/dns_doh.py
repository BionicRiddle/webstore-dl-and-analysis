import socket
import subprocess
import re
import ssl
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler

# Function to get default DNS server in Windows
def get_default_dns_windows():
    try:
        ipconfig_output = subprocess.check_output(['ipconfig', '/all'], universal_newlines=True)
        dns_servers = re.findall(r'DNS Servers .+?: ((?:\d{1,3}\.){3}\d{1,3})', ipconfig_output)
        if dns_servers:
            return dns_servers[0]
        else:
            return None
    except Exception as e:
        print("Error getting default DNS:", e)
        return None

DEFAULT_DNS_SERVER = get_default_dns_windows()
LISTEN_PORT = 53

class DNSOverHTTPSRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        dns_request = base64.urlsafe_b64decode(post_data)
        response = forward_dns(dns_request)
        self.send_response(200)
        self.send_header('Content-type', 'application/dns-message')
        self.end_headers()
        self.wfile.write(response)

def forward_dns(data):
    # Create a socket to communicate with the default DNS server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (DEFAULT_DNS_SERVER, LISTEN_PORT))
    response, _ = sock.recvfrom(1024)
    sock.close()
    return response

def start_doh_server():
    import ssl
    import pathlib
    
    httpd = HTTPServer(('127.0.0.1', 443), DNSOverHTTPSRequestHandler)
    
    # Load SSL certificate and key
    certfile = pathlib.Path('cert/server.crt')
    keyfile = pathlib.Path('cert/server.key')
    
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print("DoH server started on port 443")
    httpd.serve_forever()

def main():
    if not DEFAULT_DNS_SERVER:
        print("Unable to determine default DNS server.")
        return

    # Start the DoH server in a separate thread
    import threading
    doh_thread = threading.Thread(target=start_doh_server)
    doh_thread.daemon = True
    doh_thread.start()

    # Create a UDP socket to listen for DNS requests
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', LISTEN_PORT))  # Listen on all interfaces on port 53

    print("DNS forwarder listening on port", LISTEN_PORT)
    print("Default DNS server:", DEFAULT_DNS_SERVER)

    while True:
        data, addr = server_socket.recvfrom(1024)
        print("Received DNS request from:", addr)

        # Extract the DNS request from the data
        # (DNS request is the first 12 bytes of the data)
        dns_request = data[:12]

        # Extract domain name from DNS request
        domain_name = extract_domain_name(data[12:])

        print("Requested Domain:", domain_name)

        # Forward the DNS request to the default DNS server
        response = forward_dns(dns_request)

        # Log the request and response
        print("Request:", dns_request.hex())
        print("Response:", response.hex())

        # Send the DNS response back to the client
        server_socket.sendto(response, addr)

def extract_domain_name(data):
    domain_name = ''
    i = 0
    while True:
        length = data[i]
        if length == 0:
            break
        domain_name += data[i+1:i+1+length].decode('utf-8') + '.'
        i += length + 1
    return domain_name[:-1]

if __name__ == "__main__":
    main()
