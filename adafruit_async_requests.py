# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
# SPDX-FileContributor: Updated and repackaged/tested by Alex Herrmann, 2022
#
# SPDX-License-Identifier: MIT

"""
`adafruit_requests.async_session`
================================================================================

"""

import errno

import json as json_module

import asyncio
from adafruit_requests import Session, Response, OutOfRetries

try:
    from typing import Any, Dict, List, Optional
    from circuitpython_typing.socket import (
        SocketType,
        SocketpoolModuleType,
        SSLContextType,
    )
except ImportError:
    pass


class AsyncSession(Session):
    """HTTP session that shares sockets and ssl context."""

    def __init__(
            self,
            socket_pool: SocketpoolModuleType,
            ssl_context: Optional[SSLContextType] = None,
    ) -> None:
        Session.__init__(socket_pool, ssl_context)
        self._last_response = None

    @staticmethod
    async def _asend(socket: SocketType, data: bytes):
        total_sent = 0
        while total_sent < len(data):
            # ESP32SPI sockets raise a RuntimeError when unable to send.
            try:
                sent = socket.send(data[total_sent:])
            except OSError as exc:
                if exc.errno == errno.EAGAIN:
                    # Can't send right now (e.g., no buffer space), try again.
                    await asyncio.sleep(0)
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


    async def _asend_request(
            self,
            socket: SocketType,
            host: str,
            method: str,
            path: str,
            headers: List[Dict[str, str]],
            data: Any,
            json: Any,
    ):
        # pylint: disable=too-many-arguments
        await self._asend(socket, bytes(method, "utf-8"))
        await self._asend(socket, b" /")
        await self._asend(socket, bytes(path, "utf-8"))
        await self._asend(socket, b" HTTP/1.1\r\n")
        if "Host" not in headers:
            await self._asend(socket, b"Host: ")
            await self._asend(socket, bytes(host, "utf-8"))
            await self._asend(socket, b"\r\n")
        if "User-Agent" not in headers:
            await self._asend(socket, b"User-Agent: Adafruit CircuitPython\r\n")
        # Iterate over keys to avoid tuple alloc
        for k in headers:
            await self._asend(socket, k.encode())
            await self._asend(socket, b": ")
            await self._asend(socket, headers[k].encode())
            await self._asend(socket, b"\r\n")
        if json is not None:
            assert data is None
            data = json_module.dumps(json)
            await self._asend(socket, b"Content-Type: application/json\r\n")
        if data:
            if isinstance(data, dict):
                await self._asend(
                    socket, b"Content-Type: application/x-www-form-urlencoded\r\n"
                )
                _post_data = ""
                for k in data:
                    _post_data = "{}&{}={}".format(_post_data, k, data[k])
                data = _post_data[1:]
            await self._asend(socket, b"Content-Length: %d\r\n" % len(data))
        await self._asend(socket, b"\r\n")
        if data:
            if isinstance(data, bytearray):
                await self._asend(socket, bytes(data))
            else:
                await self._asend(socket, bytes(data, "utf-8"))

    # pylint: disable=too-many-branches, too-many-statements, unused-argument, too-many-arguments, too-many-locals
    async def arequest(
            self,
            method: str,
            url: str,
            data: Optional[Any] = None,
            json: Optional[Any] = None,
            headers: Optional[List[Dict[str, str]]] = None,
            stream: bool = False,
            timeout: float = 60,
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
        while retry_count < 2:
            retry_count += 1
            socket = self._get_socket(host, port, proto, timeout=timeout)
            ok = True
            try:
                await self._asend_request(socket, host, method, path, headers, data, json)
            except OSError:
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
            self._close_socket(socket)
            socket = None

        if not socket:
            raise OutOfRetries("Repeated socket failures")

        resp = Response(socket, self)  # our response
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

    async def ahead(self, url: str, **kw) -> Response:
        """Send HTTP HEAD request"""
        return await self.arequest("HEAD", url, **kw)

    async def aget(self, url: str, **kw) -> Response:
        """Send HTTP GET request"""
        return await self.arequest("GET", url, **kw)

    async def apost(self, url: str, **kw) -> Response:
        """Send HTTP POST request"""
        return await self.arequest("POST", url, **kw)

    async def aput(self, url: str, **kw) -> Response:
        """Send HTTP PUT request"""
        return await self.arequest("PUT", url, **kw)

    async def apatch(self, url: str, **kw) -> Response:
        """Send HTTP PATCH request"""
        return await self.arequest("PATCH", url, **kw)

    async def adelete(self, url: str, **kw) -> Response:
        """Send HTTP DELETE request"""
        return await self.arequest("DELETE", url, **kw)
