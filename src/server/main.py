import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import multiprocessing
import logging
import colorlog
import os
from datetime import datetime
from pymongo import MongoClient

PUBLIC_DIR = 'src/public'
SOCKET_SERVER_ADDR = ('localhost', 5000)
WEB_SERVER_ADDR = ('', 3000)

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """
        Handle POST requests: parse data, send it to the socket server, and redirect to the home page.
        """
        logging.debug(f"Received POST request from {self.client_address}")
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        
        logging.debug(f"Parsed data: {data_dict}")
        
        # Send data to Socket server
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(str(data_dict).encode(), SOCKET_SERVER_ADDR)
            logging.debug(f"Sent data to socket server at {SOCKET_SERVER_ADDR}")
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        """
        Handle GET requests: serve HTML or static files based on the request path.
        """
        logging.debug(f"Received GET request for {self.path} from {self.client_address}")
        pr_url = urllib.parse.urlparse(self.path)
        if (pr_url.path == '/'):
            self.send_html_file('index.html')
        elif (pr_url.path == '/message.html'):
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(PUBLIC_DIR, pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        """
        Serve an HTML file with the given status code.
        
        :param filename: Name of the HTML file to serve.
        :param status: HTTP status code to send.
        """
        logging.debug(f"Serving HTML file: {filename} with status {status}")
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(f'{PUBLIC_DIR}/{filename}', 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        """
        Serve static files based on the request path.
        """
        logging.debug(f"Serving static file: {self.path}")
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'{PUBLIC_DIR}{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def configure_logging():
    """
    Configure logging with colored output based on the LOG_LEVEL environment variable.
    """
    log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    logging.basicConfig(level=getattr(logging, log_level, logging.DEBUG), handlers=[handler])

def get_mongodb():
    """
    Get MongoDB client and collection using environment variables
    """
    user = os.getenv('MONGO_USER', 'admin')
    password = os.getenv('MONGO_PASSWORD', 'password')
    host = os.getenv('MONGO_HOST', 'localhost')
    port = os.getenv('MONGO_PORT', '27017')
    
    client = MongoClient(f'mongodb://{user}:{password}@{host}:{port}/')
    db = client['messages_db']
    return db.messages

def run_http_server():
    """
    Start the HTTP server and serve requests indefinitely.
    """
    configure_logging()
    logging.info("Starting HTTP server")
    http = HTTPServer(WEB_SERVER_ADDR, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()
        logging.info("HTTP server stopped")

def run_socket_server():
    """
    Start the socket server and listen for incoming data indefinitely.
    """
    configure_logging()
    logging.info("Starting Socket server")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SOCKET_SERVER_ADDR)
    
    # Get MongoDB collection
    messages = get_mongodb()
    
    try:
        while True:
            data, _ = sock.recvfrom(1024)
            data_dict = eval(data.decode())
            
            # Create message document with formatted date
            message = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "username": data_dict.get('username', 'anonymous'),
                "message": data_dict.get('message', '')
            }
            
            # Store in MongoDB
            messages.insert_one(message)
            logging.info(f"Stored message in MongoDB: {message}")
            
    except KeyboardInterrupt:
        logging.info("Socket server interrupted")
    finally:
        sock.close()
        logging.info("Socket server stopped")

def main():
    """
    Main entry point for starting the HTTP and Socket servers.
    """
    configure_logging()
    logging.info("Starting servers")

    http_process = multiprocessing.Process(target=run_http_server)
    socket_process = multiprocessing.Process(target=run_socket_server)
    
    http_process.start()
    socket_process.start()
    
    try:
        http_process.join()
        socket_process.join()
    except KeyboardInterrupt:
        logging.info("Stopping servers")
        http_process.terminate()
        socket_process.terminate()
        http_process.join()
        socket_process.join()
        logging.info("Servers stopped")

if __name__ == '__main__':
    main()
