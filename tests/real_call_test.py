# SPDX-FileCopyrightText: 2024 Justin Myers
#
# SPDX-License-Identifier: Unlicense

"""Real call Tests"""

import socket
import ssl

import adafruit_connection_manager
import pytest

import adafruit_requests


@pytest.mark.parametrize(
    ("path", "status_code", "text_result", "json_keys"),
    (
        ("get", 200, None, {"url": "https://httpbin.org/get"}),
        ("status/200", 200, "", None),
        ("status/204", 204, "", None),
    ),
)
def test_gets(path, status_code, text_result, json_keys):
    requests = adafruit_requests.Session(socket, ssl.create_default_context())
    with requests.get(f"https://httpbin.org/{path}") as response:
        assert response.status_code == status_code
        if text_result is not None:
            assert response.text == text_result
        if json_keys is not None:
            for key, value in json_keys.items():
                assert response.json()[key] == value

    adafruit_connection_manager.connection_manager_close_all(release_references=True)
