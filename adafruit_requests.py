# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_requests`
================================================================================

A requests-like library for web interfacing


* Author(s): ladyada, Paul Sokolovsky, Scott Shawcroft

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

* Adafruit's Connection Manager library:
  https://github.com/adafruit/Adafruit_CircuitPython_ConnectionManager

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Requests.git"

import errno
import sys

import json as json_module

from adafruit_connection_manager import get_connection_manager

if not sys.implementation.name == "circuitpython":
    from types import TracebackType
    from typing import Any, Dict, Optional, Type
    from adafruit_connection_manager import (
        SocketType,
        SocketpoolModuleType,
        SSLContextType,
    )


class _RawResponse:
    def __init__(self, response: "Response") -> None:
        self._response = response

    def read(self, size: int = -1) -> bytes:
        """Read as much as available or up to size and return it in a byte string.

        Do NOT use this unless you really need to. Reusing memory with `readinto` is much better.
        """
        if size == -1:
            return self._response.content
        return self._response.socket.recv(size)

    def readinto(self, buf: bytearray) -> int:
        """Read as much as available into buf or until it is full. Returns the number of bytes read
        into buf."""
        return self._response._readinto(buf)  # pylint: disable=protected-access


class OutOfRetries(Exception):
    """Raised when requests has retried to make a request unsuccessfully."""


class Response:
    """The response from a request, contains all the headers/content"""

    # pylint: disable=too-many-instance-attributes

    encoding = None

    def __init__(self, sock: SocketType, session: Optional["Session"] = None) -> None:
        self.socket = sock
        self.encoding = "utf-8"
        self._cached = None
        self._headers = {}

        # _start_index and _receive_buffer are used when parsing headers.
        # _receive_buffer will grow by 32 bytes everytime it is too small.
        self._received_length = 0
        self._receive_buffer = bytearray(32)
        self._remaining = None
        self._chunked = False

        http = self._readto(b" ")
        if not http:
            if session:
                session._connection_manager.close_socket(self.socket)
            else:
                self.socket.close()
            raise RuntimeError("Unable to read HTTP response.")
        self.status_code: int = int(bytes(self._readto(b" ")))
        """The status code returned by the server"""
        self.reason: bytearray = self._readto(b"\r\n")
        """The status reason returned by the server"""
        self._parse_headers()
        self._raw = None
        self._session = session

    def __enter__(self) -> "Response":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[type]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()

    def _recv_into(self, buf: bytearray, size: int = 0) -> int:
        return self.socket.recv_into(buf, size)

    def _readto(self, stop: bytes) -> bytearray:
        buf = self._receive_buffer
        end = self._received_length
        while True:
            i = buf.find(stop, 0, end)
            if i >= 0:
                # Stop was found. Return everything up to but not including stop.
                result = buf[:i]
                new_start = i + len(stop)
                # Remove everything up to and including stop from the buffer.
                new_end = end - new_start
                buf[:new_end] = buf[new_start:end]
                self._received_length = new_end
                return result

            # Not found so load more bytes.
            # If our buffer is full, then make it bigger to load more.
            if end == len(buf):
                new_buf = bytearray(len(buf) + 32)
                new_buf[: len(buf)] = buf
                buf = new_buf
                self._receive_buffer = buf

            read = self._recv_into(memoryview(buf)[end:])
            if read == 0:
                self._received_length = 0
                return buf[:end]
            end += read

    def _read_from_buffer(
        self, buf: Optional[bytearray] = None, nbytes: Optional[int] = None
    ) -> int:
        if self._received_length == 0:
            return 0
        read = self._received_length
        if nbytes < read:
            read = nbytes
        membuf = memoryview(self._receive_buffer)
        if buf:
            buf[:read] = membuf[:read]
        if read < self._received_length:
            new_end = self._received_length - read
            self._receive_buffer[:new_end] = membuf[read : self._received_length]
            self._received_length = new_end
        else:
            self._received_length = 0
        return read

    def _readinto(self, buf: bytearray) -> int:
        if not self.socket:
            raise RuntimeError(
                "Newer Response closed this one. Use Responses immediately."
            )

        if not self._remaining:
            # Consume the chunk header if need be.
            if self._chunked:
                # Consume trailing \r\n for chunks 2+
                if self._remaining == 0:
                    self._throw_away(2)
                chunk_header = bytes(self._readto(b"\r\n")).split(b";", 1)[0]
                http_chunk_size = int(bytes(chunk_header), 16)
                if http_chunk_size == 0:
                    self._chunked = False
                    self._parse_headers()
                    return 0
                self._remaining = http_chunk_size
            elif self._remaining is None:
                # the Content-Length is not provided in the HTTP header
                # so try parsing as long as their is data in the socket
                pass
            else:
                return 0

        nbytes = len(buf)
        if self._remaining and nbytes > self._remaining:
            # if Content-Length was provided and remaining bytes larges than buffer
            nbytes = self._remaining  # adjust read amount

        read = self._read_from_buffer(buf, nbytes)
        if read == 0:
            read = self._recv_into(buf, nbytes)
        if self._remaining:
            # if Content-Length was provided, adjust the remaining amount to still read
            self._remaining -= read

        return read

    def _throw_away(self, nbytes: int) -> None:
        nbytes -= self._read_from_buffer(nbytes=nbytes)

        buf = self._receive_buffer
        len_buf = len(buf)
        for _ in range(nbytes // len_buf):
            to_read = len_buf
            while to_read > 0:
                to_read -= self._recv_into(buf, to_read)
        to_read = nbytes % len_buf
        while to_read > 0:
            to_read -= self._recv_into(buf, to_read)

    def close(self) -> None:
        """Drain the remaining ESP socket buffers. We assume we already got what we wanted."""
        if not self.socket:
            return
        # Make sure we've read all of our response.
        if self._cached is None:
            if self._remaining and self._remaining > 0:
                self._throw_away(self._remaining)
            elif self._chunked:
                while True:
                    chunk_header = bytes(self._readto(b"\r\n")).split(b";", 1)[0]
                    chunk_size = int(bytes(chunk_header), 16)
                    if chunk_size == 0:
                        break
                    self._throw_away(chunk_size + 2)
                self._parse_headers()
        if self._session:
            # pylint: disable=protected-access
            self._session._connection_manager.free_socket(self.socket)
        else:
            self.socket.close()
        self.socket = None

    def _parse_headers(self) -> None:
        """
        Parses the header portion of an HTTP request/response from the socket.
        Expects first line of HTTP request/response to have been read already.
        """
        while True:
            header = self._readto(b"\r\n")
            if not header:
                break
            title, content = bytes(header).split(b": ", 1)
            if title and content:
                # enforce that all headers are lowercase
                title = str(title, "utf-8").lower()
                content = str(content, "utf-8")
                if title == "content-length":
                    self._remaining = int(content)
                if title == "transfer-encoding":
                    self._chunked = content.strip().lower() == "chunked"
                if title == "set-cookie" and title in self._headers:
                    self._headers[title] += ", " + content
                else:
                    self._headers[title] = content

    def _validate_not_gzip(self) -> None:
        """gzip encoding is not supported. Raise an exception if found."""
        if (
            "content-encoding" in self.headers
            and self.headers["content-encoding"] == "gzip"
        ):
            raise ValueError(
                "Content-encoding is gzip, data cannot be accessed as json or text. "
                "Use content property to access raw bytes."
            )

    @property
    def headers(self) -> Dict[str, str]:
        """
        The response headers. Does not include headers from the trailer until
        the content has been read.
        """
        return self._headers

    @property
    def content(self) -> bytes:
        """The HTTP content direct from the socket, as bytes"""
        if self._cached is not None:
            if isinstance(self._cached, bytes):
                return self._cached
            raise RuntimeError("Cannot access content after getting text or json")

        self._cached = b"".join(self.iter_content(chunk_size=32))
        return self._cached

    @property
    def text(self) -> str:
        """The HTTP content, encoded into a string according to the HTTP
        header encoding"""
        if self._cached is not None:
            if isinstance(self._cached, str):
                return self._cached
            raise RuntimeError("Cannot access text after getting content or json")

        self._validate_not_gzip()

        self._cached = str(self.content, self.encoding)
        return self._cached

    def json(self) -> Any:
        """The HTTP content, parsed into a json dictionary"""
        # The cached JSON will be a list or dictionary.
        if self._cached:
            if isinstance(self._cached, (list, dict)):
                return self._cached
            raise RuntimeError("Cannot access json after getting text or content")
        if not self._raw:
            self._raw = _RawResponse(self)

        self._validate_not_gzip()

        obj = json_module.load(self._raw)
        if not self._cached:
            self._cached = obj
        self.close()
        return obj

    def iter_content(self, chunk_size: int = 1, decode_unicode: bool = False) -> bytes:
        """An iterator that will stream data by only reading 'chunk_size'
        bytes and yielding them, when we can't buffer the whole datastream"""
        if decode_unicode:
            raise NotImplementedError("Unicode not supported")

        b = bytearray(chunk_size)
        while True:
            size = self._readinto(b)
            if size == 0:
                break
            if size < chunk_size:
                chunk = bytes(memoryview(b)[:size])
            else:
                chunk = bytes(b)
            yield chunk
        self.close()


_global_session = None  # pylint: disable=invalid-name


class Session:
    """HTTP session that shares sockets and ssl context."""

    def __init__(
        self,
        socket_pool: SocketpoolModuleType,
        ssl_context: Optional[SSLContextType] = None,
        set_global_session: bool = True,
    ) -> None:
        self._connection_manager = get_connection_manager(socket_pool)
        self._ssl_context = ssl_context
        self._last_response = None

        if set_global_session:
            # pylint: disable=global-statement
            global _global_session
            _global_session = self

    @staticmethod
    def _send(socket: SocketType, data: bytes):
        total_sent = 0
        while total_sent < len(data):
            # ESP32SPI sockets raise a RuntimeError when unable to send.
            try:
                sent = socket.send(data[total_sent:])
            except OSError as exc:
                if exc.errno == errno.EAGAIN:
                    # Can't send right now (e.g., no buffer space), try again.
                    continue
                # Some worse error.
                raise
            except RuntimeError as exc:
                raise OSError(errno.EIO) from exc
            if sent is None:
                sent = len(data)
            if sent == 0:
                # Not EAGAIN; that was already handled.
                raise OSError(errno.EIO)
            total_sent += sent

    def _send_as_bytes(self, socket: SocketType, data: str):
        return self._send(socket, bytes(data, "utf-8"))

    def _send_header(self, socket, header, value):
        self._send_as_bytes(socket, header)
        self._send(socket, b": ")
        self._send_as_bytes(socket, value)
        self._send(socket, b"\r\n")

    # pylint: disable=too-many-arguments
    def _send_request(
        self,
        socket: SocketType,
        host: str,
        method: str,
        path: str,
        headers: Dict[str, str],
        data: Any,
        json: Any,
    ):
        # Convert data
        content_type_header = None

        # If json is sent, set content type header and convert to string
        if json is not None:
            assert data is None
            content_type_header = "application/json"
            data = json_module.dumps(json)

        # If data is sent and it's a dict, set content type header and convert to string
        if data and isinstance(data, dict):
            content_type_header = "application/x-www-form-urlencoded"
            _post_data = ""
            for k in data:
                _post_data = "{}&{}={}".format(_post_data, k, data[k])
            # remove first "&" from concatenation
            data = _post_data[1:]

        # Convert str data to bytes
        if data and isinstance(data, str):
            data = bytes(data, "utf-8")

        self._send_as_bytes(socket, method)
        self._send(socket, b" /")
        self._send_as_bytes(socket, path)
        self._send(socket, b" HTTP/1.1\r\n")

        # create lower-case supplied header list
        supplied_headers = {header.lower() for header in headers}

        # Send headers
        if not "host" in supplied_headers:
            self._send_header(socket, "Host", host)
        if not "user-agent" in supplied_headers:
            self._send_header(socket, "User-Agent", "Adafruit CircuitPython")
        if content_type_header and not "content-type" in supplied_headers:
            self._send_header(socket, "Content-Type", content_type_header)
        if data and not "content-length" in supplied_headers:
            self._send_header(socket, "Content-Length", str(len(data)))
        # Iterate over keys to avoid tuple alloc
        for header in headers:
            self._send_header(socket, header, headers[header])
        self._send(socket, b"\r\n")

        # Send data
        if data:
            self._send(socket, bytes(data))

    # pylint: disable=too-many-branches, too-many-statements, unused-argument, too-many-arguments, too-many-locals
    def request(
        self,
        method: str,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
        timeout: float = 60,
        allow_redirects: bool = True,
    ) -> Response:
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
            self._last_response.close()
            self._last_response = None

        # We may fail to send the request if the socket we got is closed already. So, try a second
        # time in that case.
        retry_count = 0
        last_exc = None
        while retry_count < 2:
            retry_count += 1
            socket = self._connection_manager.get_socket(
                host, port, proto, timeout=timeout, ssl_context=self._ssl_context
            )
            ok = True
            try:
                self._send_request(socket, host, method, path, headers, data, json)
            except OSError as exc:
                last_exc = exc
                ok = False
            if ok:
                # Read the H of "HTTP/1.1" to make sure the socket is alive. send can appear to work
                # even when the socket is closed.
                if hasattr(socket, "recv"):
                    result = socket.recv(1)
                else:
                    result = bytearray(1)
                    try:
                        socket.recv_into(result)
                    except OSError:
                        pass
                if result == b"H":
                    # Things seem to be ok so break with socket set.
                    break
            self._connection_manager.close_socket(socket)
            socket = None

        if not socket:
            raise OutOfRetries("Repeated socket failures") from last_exc

        resp = Response(socket, self)  # our response
        if allow_redirects:
            if "location" in resp.headers and 300 <= resp.status_code <= 399:
                # a naive handler for redirects
                redirect = resp.headers["location"]

                if redirect.startswith("http"):
                    # absolute URL
                    url = redirect
                elif redirect[0] == "/":
                    # relative URL, absolute path
                    url = "/".join([proto, dummy, host, redirect[1:]])
                else:
                    # relative URL, relative path
                    path = path.rsplit("/", 1)[0]

                    while redirect.startswith("../"):
                        path = path.rsplit("/", 1)[0]
                        redirect = redirect.split("../", 1)[1]

                    url = "/".join([proto, dummy, host, path, redirect])

                self._last_response = resp
                resp = self.request(method, url, data, json, headers, stream, timeout)

        self._last_response = resp
        return resp

    def head(self, url: str, **kw) -> Response:
        """Send HTTP HEAD request"""
        return self.request("HEAD", url, **kw)

    def get(self, url: str, **kw) -> Response:
        """Send HTTP GET request"""
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw) -> Response:
        """Send HTTP POST request"""
        return self.request("POST", url, **kw)

    def put(self, url: str, **kw) -> Response:
        """Send HTTP PUT request"""
        return self.request("PUT", url, **kw)

    def patch(self, url: str, **kw) -> Response:
        """Send HTTP PATCH request"""
        return self.request("PATCH", url, **kw)

    def delete(self, url: str, **kw) -> Response:
        """Send HTTP DELETE request"""
        return self.request("DELETE", url, **kw)


def request(
    method: str,
    url: str,
    data: Optional[Any] = None,
    json: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    stream: bool = False,
    timeout: float = 1,
) -> None:
    """Send HTTP request"""
    # pylint: disable=too-many-arguments
    _global_session.request(
        method,
        url,
        data=data,
        json=json,
        headers=headers,
        stream=stream,
        timeout=timeout,
    )


def head(url: str, **kw):
    """Send HTTP HEAD request"""
    return _global_session.request("HEAD", url, **kw)


def get(url: str, **kw):
    """Send HTTP GET request"""
    return _global_session.request("GET", url, **kw)


def post(url: str, **kw):
    """Send HTTP POST request"""
    return _global_session.request("POST", url, **kw)


def put(url: str, **kw):
    """Send HTTP PUT request"""
    return _global_session.request("PUT", url, **kw)


def patch(url: str, **kw):
    """Send HTTP PATCH request"""
    return _global_session.request("PATCH", url, **kw)


def delete(url: str, **kw):
    """Send HTTP DELETE request"""
    return _global_session.request("DELETE", url, **kw)
