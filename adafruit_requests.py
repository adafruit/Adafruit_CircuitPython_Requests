# The MIT License (MIT)
#
# Copyright (c) 2019 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_requests`
================================================================================

A requests-like library for web interfacing


* Author(s): ladyada, Paul Sokolovsky

Implementation Notes
--------------------

Adapted from https://github.com/micropython/micropython-lib/tree/master/urequests

micropython-lib consists of multiple modules from different sources and
authors. Each module comes under its own licensing terms. Short name of
a license can be found in a file within a module directory (usually
metadata.txt or setup.py). Complete text of each license used is provided
at https://github.com/micropython/micropython-lib/blob/master/LICENSE

author='Paul Sokolovsky'
license='MIT'

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import gc

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Requests.git"

# This module mirror CPython's socket class. It is settable because the network devices are external
# to CircuitPython.
_socket = None  # pylint: disable=invalid-name


def set_socket(socket):
    """Helper to set the global socket.
    :param sock: socket module

    """
    global _socket  # pylint: disable=invalid-name, global-statement
    _socket = socket

# Hang onto open sockets so that we can reuse them.
_socket_pool = {}
def _get_socket(host, port, proto, *, timeout=1):
    key = (host, port, proto)
    if key in _socket_pool:
        socket = _socket_pool[key]
        if not socket.connected():
            del _socket_pool[key]
        else:
            return socket
    addr_info = _socket.getaddrinfo(host, port, 0, _socket.SOCK_STREAM)[0]
    sock = _socket.socket(addr_info[0], addr_info[1], addr_info[2])
    sock.settimeout(timeout)  # socket read timeout

    if proto == "https:":
        # for SSL we need to know the host name
        sock.connect((host, port), _socket.TLS_MODE)
    else:
        sock.connect(addr_info[-1], _socket.TCP_MODE)
    _socket_pool[key] = sock
    return sock


class Response:
    """The response from a request, contains all the headers/content"""

    encoding = None

    def __init__(self, sock):
        self.socket = sock
        self.encoding = "utf-8"
        self._cached = None
        self._headers = {}

        if not self.socket.connected():
            raise RuntimeError("We were too slow")

        line = self.socket.readline()
        if line is None:
            raise RuntimeError("Unable to read HTTP response.")
        line = line.split(b" ", 2)
        self.status_code = int(line[1])
        self.reason = ""
        if len(line) > 2:
            self.reason = line[2].rstrip()
        self._parse_headers()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """Close, delete and collect the response data"""
        if self.socket:
            # Make sure we've read all of our response.
            content_length = None
            if "content-length" in self.headers:
                content_length = int(self.headers["content-length"])

            # print("Content length:", content_length)
            if self._cached is None:
                if content_length:
                    self.socket.recv(content_length)
                else:
                    while True:
                        chunk_header = self.socket.readline()
                        if b";" in chunk_header:
                            chunk_header = chunk_header.split(b";")[0]
                        chunk_size = int(chunk_header, 16)
                        if chunk_size == 0:
                            break
                        self.socket.read(chunk_size + 2)
                    self._parse_headers()
                self.socket = None
        del self._cached
        gc.collect()

    def _parse_headers(self):
        """
        Parses the header portion of an HTTP request/response from the socket.
        Expects first line of HTTP request/response to have been read already.
        """
        while True:
            line = self.socket.readline()
            if not line or line == b"\r\n":
                break

            #print("**line: ", line)
            splits = line.split(b': ', 1)
            title = splits[0]
            content = ''
            if len(splits) > 1:
                content = splits[1]
            if title and content:
                title = str(title.lower(), 'utf-8')
                content = str(content, 'utf-8')
                self._headers[title] = content

    @property
    def headers(self):
        return self._headers

    @property
    def content(self):
        """The HTTP content direct from the socket, as bytes"""
        # print(self.headers)
        content_length = None
        if "content-length" in self.headers:
            content_length = int(self.headers["content-length"])

        # print("Content length:", content_length)
        if self._cached is None:
            if content_length:
                self._cached = self.socket.recv(content_length)
            else:
                chunks = []
                while True:
                    chunk_header = self.socket.readline()
                    if chunk_header is None:
                        raise RuntimeError("Reading content timed out.")
                    if b";" in chunk_header:
                        chunk_header = chunk_header.split(b";")[0]
                    chunk_size = int(chunk_header, 16)
                    if chunk_size == 0:
                        break
                    chunks.append(self.socket.read(chunk_size))
                    self.socket.read(2) # Read the trailing CR LF
                self._parse_headers()
                self._cached = b"".join(chunks)
            self.socket = None

        # print("Buffer length:", len(self._cached))
        return self._cached

    @property
    def text(self):
        """The HTTP content, encoded into a string according to the HTTP
        header encoding"""
        return str(self.content, self.encoding)

    def json(self):
        """The HTTP content, parsed into a json dictionary"""
        # pylint: disable=import-outside-toplevel
        try:
            import json as json_module
        except ImportError:
            import ujson as json_module

        return json_module.loads(self.content)

    def iter_content(self, chunk_size=1, decode_unicode=False):
        """An iterator that will stream data by only reading 'chunk_size'
        bytes and yielding them, when we can't buffer the whole datastream"""
        if decode_unicode:
            raise NotImplementedError("Unicode not supported")

        content_length = None
        if "content-length" in self.headers:
            content_length = int(self.headers["content-length"])

        total_read = 0
        if content_length:
            while total_read < content_length:
                chunk = self.socket.recv(chunk_size)
                total_read += chunk_size
                yield chunk
        else:
            pending_bytes = 0
            chunks = []
            while True:
                chunk_header = self.socket.readline()
                if b";" in chunk_header:
                    chunk_header = chunk_header.split(b";")[0]
                http_chunk_size = int(chunk_header, 16)
                if http_chunk_size == 0:
                    break
                remaining_in_http_chunk = http_chunk_size
                while remaining_in_http_chunk:
                    read_now = chunk_size - pending_bytes
                    if read_now > remaining_in_http_chunk:
                        read_now = remaining_in_http_chunk
                    chunks.append(self.socket.read(read_now))
                    pending_bytes += read_now
                    if pending_bytes == chunk_size:
                        yield b"".join(chunks)
                        pending_bytes = 0
                        chunks = []

                self.socket.read(2) # Read the trailing CR LF
            self._parse_headers()
            if chunks:
                yield b"".join(chunks)
        self.socket = None


# pylint: disable=too-many-branches, too-many-statements, unused-argument, too-many-arguments, too-many-locals
def request(method, url, data=None, json=None, headers=None, stream=False, timeout=60):
    """Perform an HTTP request to the given url which we will parse to determine
    whether to use SSL ('https://') or not. We can also send some provided 'data'
    or a json dictionary which we will stringify. 'headers' is optional HTTP headers
    sent along. 'stream' will determine if we buffer everything, or whether to only
    read only when requested
    """
    global _the_interface  # pylint: disable=global-statement, invalid-name
    global _socket  # pylint: disable=global-statement, invalid-name

    if not headers:
        headers = {}

    try:
        proto, dummy, host, path = url.split("/", 3)
        # replace spaces in path
        path = path.replace(" ", "%20")
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == "http:":
        port = 80
    elif proto == "https:":
        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    socket = _get_socket(host, port, proto, timeout=timeout)
    socket.send(b"%s /%s HTTP/1.1\r\n" % (bytes(method, "utf-8"), bytes(path, "utf-8")))
    if "Host" not in headers:
        socket.send(b"Host: %s\r\n" % bytes(host, "utf-8"))
    if "User-Agent" not in headers:
        socket.send(b"User-Agent: Adafruit CircuitPython\r\n")
    # Iterate over keys to avoid tuple alloc
    for k in headers:
        socket.send(k.encode())
        socket.send(b": ")
        socket.send(headers[k].encode())
        socket.send(b"\r\n")
    if json is not None:
        assert data is None
        try:
            import json as json_module
        except ImportError:
            import ujson as json_module
        data = json_module.dumps(json)
        socket.send(b"Content-Type: application/json\r\n")
    if data:
        if isinstance(data, dict):
            sock.send(b"Content-Type: application/x-www-form-urlencoded\r\n")
            _post_data = ""
            for k in data:
                _post_data = "{}&{}={}".format(_post_data, k, data[k])
            data = _post_data[1:]
        socket.send(b"Content-Length: %d\r\n" % len(data))
    socket.send(b"\r\n")
    if data:
        if isinstance(data, bytearray):
            socket.send(bytes(data))
        else:
            socket.send(bytes(data, "utf-8"))

    resp = Response(socket)  # our response
    if "location" in resp.headers and not 200 <= resp.status_code <= 299:
        raise NotImplementedError("Redirects not yet supported")

    return resp

def head(url, **kw):
    """Send HTTP HEAD request"""
    return request("HEAD", url, **kw)


def get(url, **kw):
    """Send HTTP GET request"""
    return request("GET", url, **kw)


def post(url, **kw):
    """Send HTTP POST request"""
    return request("POST", url, **kw)


def put(url, **kw):
    """Send HTTP PUT request"""
    return request("PUT", url, **kw)


def patch(url, **kw):
    """Send HTTP PATCH request"""
    return request("PATCH", url, **kw)


def delete(url, **kw):
    """Send HTTP DELETE request"""
    return request("DELETE", url, **kw)
