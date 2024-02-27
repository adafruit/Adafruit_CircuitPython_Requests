# SPDX-FileCopyrightText: 2023 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" PyTest Setup """

import adafruit_connection_manager
import mocket
import pytest

import adafruit_requests


@pytest.fixture(autouse=True)
def reset_connection_manager(monkeypatch):
    """Reset the ConnectionManager, since it's a singlton and will hold data"""
    monkeypatch.setattr(
        "adafruit_requests.get_connection_manager",
        adafruit_connection_manager.ConnectionManager,
    )


@pytest.fixture
def sock():
    return mocket.Mocket(mocket.MOCK_RESPONSE)


@pytest.fixture
def pool(sock):
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = (
        (None, None, None, None, (mocket.MOCK_POOL_IP, 80)),
    )
    pool.socket.return_value = sock
    return pool


@pytest.fixture
def requests(pool):
    return adafruit_requests.Session(pool)


@pytest.fixture
def requests_ssl(pool):
    ssl_context = mocket.SSLContext()
    return adafruit_requests.Session(pool, ssl_context)
