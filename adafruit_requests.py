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

class _RawResponse:
    def __init__(self, response):
        self._response = response

    def read(self, size=-1):
        if size == -1:
            return self.content

        return self._response.socket.recv(size)

    def readinto(self, buf):
        return self._response._readinto(buf)

class Response:
    """The response from a request, contains all the headers/content"""

    encoding = None

    def __init__(self, sock, session=None):
        self.socket = sock
        self.encoding = "utf-8"
        self._cached = None
        self._headers = {}
        # 0 means the first receive buffer is empty because we always consume some of it. non-zero
        # means we need to look at it's tail for our pattern.
        self._start_index = 0
        self._buffer_sizes = [0]
        self._receive_buffers = [bytearray(32)]
        self._content_length = None

        http = self._readto(b" ")
        if not http:
            raise RuntimeError("Unable to read HTTP response.")
        self.status_code = int(self._readto(b" "))
        self.reason = self._readto(b"\r\n")
        self._parse_headers()
        self._raw = None
        self._content_read = 0
        self._session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _readto(self, first, second=b""):
        # TODO: Make this work if either pattern spans buffers.
        if len(first) > 2 or len(second) > 2:
            raise ValueError("Pattern too long. Must be less than 3 characters.")
        current_buffer = 0
        found = -2
        new_start = 0
        if self._start_index < self._buffer_sizes[0]:
            first_i = self._receive_buffers[0].find(first, self._start_index)
            if second:
                second_i = self._receive_buffers[0].find(second, self._start_index)
                if second_i >= 0 and (first_i <= -1 or first_i > second_i):
                    found = second_i
                    new_start = second_i + len(second)

            if found == -2:
                if first_i >= 0:
                    found = first_i
                    new_start = first_i + len(first)
                else:
                    current_buffer = 1
        else:
            self._start_index = 0

        while found < -1:
            if current_buffer == len(self._receive_buffers):
                self._receive_buffers.append(bytearray(len(self._receive_buffers[0])))
                self._buffer_sizes.append(0)
            buf = self._receive_buffers[current_buffer]
            size = self.socket.recv_into(buf)
            self._buffer_sizes[current_buffer] = size

            if len(first) == 2:
                previous_size = self._buffer_sizes[current_buffer - 1]
                if (self._receive_buffers[current_buffer - 1][previous_size - 1] == first[0] and
                    buf[0] == first[1]):
                    found = -1
                    new_start = 1
                    break

            first_i = buf.find(first, 0, size)
            if second:
                if len(second) == 2:
                    previous_size = self._buffer_sizes[current_buffer - 1]
                    if (self._receive_buffers[current_buffer - 1][previous_size - 1] == second[0] and
                    buf[0] == second[1]):
                        found = -1
                        new_start = 1
                        break
                second_i = buf.find(second, 0, size)
                if second_i >= 0 and (first_i < 0 or first_i > second_i):
                    found = second_i
                    new_start = second_i + len(second)
                    break
            if first_i >= 0:
                found = first_i
                new_start = first_i + len(first)
                break
            current_buffer += 1


        if current_buffer == 0:
            b = bytes(self._receive_buffers[0][self._start_index:found])
            self._start_index = new_start
        else:
            new_len = len(self._receive_buffers[0]) * current_buffer + found - self._start_index
            b = bytearray(new_len)
            i = 0
            for bufi in range(0, current_buffer + 1):
                buf = self._receive_buffers[bufi]
                size = self._buffer_sizes[bufi]
                if bufi == 0 and self._start_index > 0:
                    i = size - self._start_index
                    b[:i] = buf[self._start_index:size]
                elif bufi == current_buffer:
                    if found > 0:
                        b[i:i+found] = buf[:found]
                else:
                    b[i:i+size] = buf[:size]
                    i += size

            self._start_index = new_start
            # Swap the current buffer to the front because it has some bytes we
            # need to search.
            last_buf = self._receive_buffers[current_buffer]
            self._receive_buffers[current_buffer] = self._receive_buffers[0]
            self._buffer_sizes[0] = self._buffer_sizes[current_buffer]
            self._receive_buffers[0] = last_buf
            self._buffer_sizes[current_buffer] = 0

        return b

    def _readinto(self, buf):
        remaining = self._content_length - self._content_read
        nbytes = len(buf)
        if nbytes > remaining:
            nbytes = remaining

        if self._start_index < self._buffer_sizes[0]:
            size = self._buffer_sizes[0]
            left = size - self._start_index
            if nbytes < left:
                left = nbytes
            start = self._start_index
            end = start + left
            if left == 1:
                buf[0] = self._receive_buffers[0][start]
            else:
                buf[:left] = self._receive_buffers[0][start:end]
            read = left
            self._start_index += left
            if read < nbytes:
                read += self.socket.recv_into(memoryview(buf)[read:nbytes])
        else:
            read = self.socket.recv_into(buf, nbytes)
        self._content_read += read
        return read

    def _throw_away(self, nbytes):
        buf = self._receive_buffers[0]
        for i in range(nbytes // len(buf)):
            self.socket.recv_into(buf)
        remaining = nbytes % len(buf)
        if remaining:
            self.socket.recv_into(buf, remaining)

    def _close(self):
        """Drain the remaining ESP socket buffers. We assume we already got what we wanted."""
        if self.socket:
            # Make sure we've read all of our response.
            # print("Content length:", content_length)
            if self._cached is None:
                remaining = self._content_length - self._content_read
                if remaining > 0:
                    self._throw_away(remaining)
                elif self._content_length is None:
                    while True:
                        chunk_header = self._readto(b";", b"\r\n")
                        chunk_size = int(chunk_header, 16)
                        if chunk_size == 0:
                            break
                        self._throw_away(chunk_size + 2)
                    self._parse_headers()
            if self._session:
                self._session.free_socket(self.socket)
            else:
                self.socket.close()
            self.socket = None

    def _parse_headers(self):
        """
        Parses the header portion of an HTTP request/response from the socket.
        Expects first line of HTTP request/response to have been read already.
        """
        while True:
            title = self._readto(b": ", b"\r\n")
            if not title:
                break

            content = self._readto(b"\r\n")
            if title and content:
                title = str(title, 'utf-8')
                content = str(content, 'utf-8')
                # Check len first so we can skip the .lower allocation most of the time.
                if len(title) == len("content-length") and title.lower() == "content-length":
                    self._content_length = int(content)
                self._headers[title] = content

    @property
    def headers(self):
        """
        The response headers. Does not include headers from the trailer until
        the content has been read.
        """
        return self._headers

    @property
    def content(self):
        """The HTTP content direct from the socket, as bytes"""
        if self._cached is not None:
            if isinstance(self._cached, bytes):
                return self._cached
            raise RuntimeError("Cannot access content after getting text or json")

        self._cached = b"".join(self.iter_content(chunk_size=32))
        return self._cached

    @property
    def text(self):
        """The HTTP content, encoded into a string according to the HTTP
        header encoding"""
        if self._cached is not None:
            if isinstance(self._cached, str):
                return self._cached
            raise RuntimeError("Cannot access text after getting content or json")
        self._cached = str(self.content, self.encoding)
        return self._cached

    def json(self):
        """The HTTP content, parsed into a json dictionary"""
        # pylint: disable=import-outside-toplevel
        import json as json_module

        # The cached JSON will be a list or dictionary.
        if self._cached:
            if isinstance(self._cached, (list, dict)):
                return self._cached
            raise RuntimeError("Cannot access json after getting text or content")
        if not self._raw:
            self._raw = _RawResponse(self)

        obj = json_module.load(self._raw)
        if not self._cached:
            self._cached = obj
        self._close()
        return obj

    def iter_content(self, chunk_size=1, decode_unicode=False):
        """An iterator that will stream data by only reading 'chunk_size'
        bytes and yielding them, when we can't buffer the whole datastream"""
        if decode_unicode:
            raise NotImplementedError("Unicode not supported")

        total_read = 0
        if self._content_length is not None:
            while self._content_read < self._content_length:
                remaining = self._content_length - self._content_read
                if chunk_size > remaining:
                    chunk_size = remaining
                b = bytearray(chunk_size)
                size = self._readinto(b)
                total_read += self._content_read
                if size < chunk_size:
                    chunk = bytes(memoryview(b)[:size])
                else:
                    chunk = bytes(b)
                yield chunk
        else:
            pending_bytes = 0
            buf = memoryview(bytearray(chunk_size))
            while True:
                chunk_header = self._readto(b";", b"\r\n")
                http_chunk_size = int(chunk_header, 16)
                if http_chunk_size == 0:
                    break
                self._content_length = http_chunk_size
                remaining_in_http_chunk = http_chunk_size
                while remaining_in_http_chunk:
                    read_now = chunk_size - pending_bytes
                    if read_now > remaining_in_http_chunk:
                        read_now = remaining_in_http_chunk
                    read_now = self._readinto(buf[pending_bytes:pending_bytes+read_now])
                    pending_bytes += read_now
                    if pending_bytes == chunk_size:
                        yield bytes(buf)
                        pending_bytes = 0

                self._throw_away(2) # Read the trailing CR LF
            self._parse_headers()
            if pending_bytes > 0:
                yield bytes(buf[:pending_bytes])
        self._close()

class Session:
    def __init__(self, socket_pool, ssl_context=None):
        self._socket_pool = socket_pool
        self._ssl_context = ssl_context
        # Hang onto open sockets so that we can reuse them.
        self._open_sockets = {}
        self._socket_free = {}
        self._last_response = None

    def free_socket(self, socket):
        if socket not in self._open_sockets.values():
            raise RuntimeError("Socket not from session")
        self._socket_free[socket] = True


    def _get_socket(self, host, port, proto, *, timeout=1):
        key = (host, port, proto)
        if key in self._open_sockets:
            sock = self._open_sockets[key]
            if self._socket_free[sock]:
                self._socket_free[sock] = False
                return sock
        if proto == "https:" and not self._ssl_context:
            raise RuntimeError("ssl_context must be set before using adafruit_requests for https")
        addr_info = self._socket_pool.getaddrinfo(host, port, 0, self._socket_pool.SOCK_STREAM)[0]
        sock = self._socket_pool.socket(addr_info[0], addr_info[1], addr_info[2])
        if proto == "https:":
            sock = self._ssl_context.wrap_socket(sock, server_hostname=host)
        sock.settimeout(timeout)  # socket read timeout
        ok = True
        try:
            sock.connect((host, port))
        except MemoryError:
            if not any(self._socket_free.items()):
                raise
            ok = False

        # We couldn't connect due to memory so clean up the open sockets.
        if not ok:
            for s in self._socket_free:
                if self._socket_free[s]:
                    s.close()
                    del self._socket_free[s]
                    for k in self._open_sockets:
                        if self._open_sockets[k] == s:
                            del self._open_sockets[k]
            # Recreate the socket because the ESP-IDF won't retry the connection if it failed once.
            sock = None # Clear first so the first socket can be cleaned up.
            sock = self._socket_pool.socket(addr_info[0], addr_info[1], addr_info[2])
            if proto == "https:":
                sock = self._ssl_context.wrap_socket(sock, server_hostname=host)
            sock.settimeout(timeout)  # socket read timeout
            sock.connect((host, port))
        self._open_sockets[key] = sock
        self._socket_free[sock] = False
        return sock

    # pylint: disable=too-many-branches, too-many-statements, unused-argument, too-many-arguments, too-many-locals
    def request(self, method, url, data=None, json=None, headers=None, stream=False, timeout=60):
        """Perform an HTTP request to the given url which we will parse to determine
        whether to use SSL ('https://') or not. We can also send some provided 'data'
        or a json dictionary which we will stringify. 'headers' is optional HTTP headers
        sent along. 'stream' will determine if we buffer everything, or whether to only
        read only when requested
        """
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

        if self._last_response:
            self._last_response._close()
            self._last_response = None

        socket = self._get_socket(host, port, proto, timeout=timeout)
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
            # pylint: disable=import-outside-toplevel
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

        resp = Response(socket, self)  # our response
        if "location" in resp.headers and not 200 <= resp.status_code <= 299:
            raise NotImplementedError("Redirects not yet supported")

        self._last_response = resp
        return resp

    def head(self, url, **kw):
        """Send HTTP HEAD request"""
        return self.request("HEAD", url, **kw)


    def get(self, url, **kw):
        """Send HTTP GET request"""
        return self.request("GET", url, **kw)


    def post(self, url, **kw):
        """Send HTTP POST request"""
        return self.request("POST", url, **kw)


    def put(self, url, **kw):
        """Send HTTP PUT request"""
        return self.request("PUT", url, **kw)


    def patch(self, url, **kw):
        """Send HTTP PATCH request"""
        return self.request("PATCH", url, **kw)


    def delete(self, url, **kw):
        """Send HTTP DELETE request"""
        return self.request("DELETE", url, **kw)
