# SPDX-FileCopyrightText: 2024 Justin Myers
#
# SPDX-License-Identifier: Unlicense

"""Real call Tests"""

import socket
import socketserver
import ssl
import threading
import time

import adafruit_connection_manager
import pytest
from local_test_server import uses_local_server

import adafruit_requests


@uses_local_server
def test_gets():
    path_index = 0
    status_code_index = 1
    text_result_index = 2
    json_keys_index = 3
    cases = [
        ("get", 200, None, {"url": "http://localhost:5000/get"}),
        ("status/200", 200, "", None),
        ("status/204", 204, "", None),
    ]

    for case in cases:
        requests = adafruit_requests.Session(socket, ssl.create_default_context())
        with requests.get(f"http://127.0.0.1:5000/{case[path_index]}") as response:
            assert response.status_code == case[status_code_index]
            if case[text_result_index] is not None:
                assert response.text == case[text_result_index]
            if case[json_keys_index] is not None:
                for key, value in case[json_keys_index].items():
                    assert response.json()[key] == value

        adafruit_connection_manager.connection_manager_close_all(release_references=True)


@pytest.mark.parametrize(
    ("allow_redirects", "status_code"),
    (
        (True, 200),
        (False, 301),
    ),
)
def test_http_to_https_redirect(allow_redirects, status_code):
    url = "http://www.adafruit.com/api/quotes.php"
    requests = adafruit_requests.Session(socket, ssl.create_default_context())
    with requests.get(url, allow_redirects=allow_redirects) as response:
        assert response.status_code == status_code


def test_https_direct():
    url = "https://www.adafruit.com/api/quotes.php"
    requests = adafruit_requests.Session(socket, ssl.create_default_context())
    with requests.get(url) as response:
        assert response.status_code == 200
