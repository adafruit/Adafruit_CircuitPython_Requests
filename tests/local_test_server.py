# SPDX-FileCopyrightText: 2025 Tim Cocks
#
# SPDX-License-Identifier: MIT
import functools
import json
import socketserver
import threading
import time
from http.server import SimpleHTTPRequestHandler


def uses_local_server(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with ReusableAddressTCPServer(("127.0.0.1", 5000), LocalTestServerHandler) as server:
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            time.sleep(2)  # Give the server some time to start

            result = func(*args, **kwargs)

            server.shutdown()
            server.server_close()
            return result

    return wrapper


class ReusableAddressTCPServer(socketserver.TCPServer):
    # Enable SO_REUSEADDR
    allow_reuse_address = True


class LocalTestServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/post":
            resp_body = json.dumps({"url": "http://localhost:5000/post"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

    def do_GET(self):
        if self.path == "/get":
            resp_body = json.dumps({"url": "http://localhost:5000/get"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        if self.path.startswith("/status"):
            try:
                requested_status = int(self.path.split("/")[2])
            except ValueError:
                resp_body = json.dumps({"error": "requested status code must be int"}).encode(
                    "utf-8"
                )
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
                return

            if requested_status != 204:
                self.send_response(requested_status)
                self.send_header("Content-type", "text/html")
                self.send_header("Content-Length", "0")
            else:
                self.send_response(requested_status)
                self.send_header("Content-type", "text/html")
            self.end_headers()
