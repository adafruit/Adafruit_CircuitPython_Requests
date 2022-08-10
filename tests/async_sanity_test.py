# SPDX-FileCopyrightText: 2022 Alex Herrmann for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Asynchronous Requests sanity tests """
import asyncio
from time import sleep
from typing import Optional, Tuple

from circuitpython_typing.socket import CircuitPythonSocketType, InterfaceType

import pytest
import socket
import mocket
import adafruit_async_requests
from adafruit_requests import SocketpoolModuleType, _FakeSSLContext, CommonSocketType

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE_HEADERS = b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n"

class IFace(InterfaceType):
    @property
    def TLS_MODE(self) -> int:
        return 1

class SlowReceivingSocket(mocket.Mocket):


    """A socket that delays before it "recvs" bytes """

    def __init__(self, response, delay=2):
        super().__init__(response)
        self._delay = delay

    def _recv(self, count):
        sleep(self._delay)
        return super()._recv(count)

    def _recv_into(self, buf, nbytes=0):
        sleep(self._delay)
        return super()._recv_into(buf, nbytes)


@pytest.mark.timeout(3)
def test_sanity_3():
    asyncio.run(three(), debug=True)



async def three():
    """
    This test will start 3 gets and awaits them out of order. It's naive and not super helpful
    """
    # This doesn't actually do anything
    delayUrl = f"https://{HOST}/delay/5"
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock: lambda: CommonSocketType = lambda: mocket.Mocket(b"""HTTP/1.0 200 OK\r\nContent-Length: 4\r\n\r\n1234""")

    # We're gonna ask for three sockets in a row
    sock1 = sock()
    sock2 = sock()
    sock3 = sock()
    pool.socket.side_effect = [sock1, sock2, sock3]

    requests_session = adafruit_async_requests.AsyncSession(pool)

    # Purposefully NOT awaiting these

    task1 = requests_session.aget("http://" + HOST + "/get")
    task2 = requests_session.aget("http://" + HOST + "/get")
    task3 = requests_session.aget("http://" + HOST + "/get")

    response3 = await task3
    assert b"1234" in response3.content
    await task2
    await task1

    sock3.connect.assert_called_once()
    sock2.connect.assert_called_once()
    sock1.connect.assert_called_once()



@pytest.mark.asyncio
async def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_async_requests.AsyncSession(pool)

    headers = {"user-agent": "blinka/1.0.0"}
    await requests_session.aget("http://" + HOST + "/get", headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent).lower()
    assert b"user-agent: blinka/1.0.0\r\n" in sent