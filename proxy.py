#!/usr/bin/env python3
"""
Simple HTTP proxy to redirect requests from localhost:8000 to localhost:8001
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import sys

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()

    def do_POST(self):
        self.proxy_request()

    def do_PUT(self):
        self.proxy_request()

    def do_DELETE(self):
        self.proxy_request()

    def do_PATCH(self):
        self.proxy_request()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def proxy_request(self):
        target_url = f"http://localhost:8001{self.path}"

        try:
            # Read request body for POST/PUT/PATCH
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Create new request
            req = urllib.request.Request(target_url, body, headers=self.headers)

            # Get method and set it
            req.get_method = lambda: self.command

            # Make the request
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.getcode())

                # Send response headers
                for header, value in response.headers.items():
                    if header.lower() != 'content-encoding' and header.lower() != 'transfer-encoding':
                        self.send_header(header, value)

                # Add CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

                self.end_headers()

                # Send response body
                self.wfile.write(response.read())

        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal Server Error')

if __name__ == '__main__':
    port = 8000
    print(f"Starting proxy server on port {port}")
    print(f"Redirecting all requests to localhost:8001")

    server = HTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"Proxy server running at http://localhost:{port}")
    server.serve_forever()