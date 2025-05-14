import http.server
import socketserver
import socket

PORT = 8080
DIRECTORY = "firmware"

class OTAHandler(http.server.SimpleHTTPRequestHandler):  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/ack":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            print(f"Received OTA ACK: {post_data}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ACK received")
        else:
            self.send_response(404)
            self.end_headers()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    with socketserver.TCPServer(("", PORT), OTAHandler) as httpd:
        print(f"Serving OTA files at http://{local_ip}:{PORT}")
        httpd.serve_forever()
