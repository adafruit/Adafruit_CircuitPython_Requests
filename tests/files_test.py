# SPDX-FileCopyrightText: 2024 Justin Myers
#
# SPDX-License-Identifier: Unlicense

""" Post Files Tests """
# pylint: disable=line-too-long

import re
from unittest import mock

import mocket
import pytest
import requests as python_requests


@pytest.fixture
def log_stream():
    return []


@pytest.fixture
def post_url():
    return "https://httpbin.org/post"


@pytest.fixture
def request_logging(log_stream):
    """Reset the ConnectionManager, since it's a singlton and will hold data"""
    import http.client  # pylint: disable=import-outside-toplevel

    def httpclient_log(*args):
        log_stream.append(args)

    http.client.print = httpclient_log
    http.client.HTTPConnection.debuglevel = 1


def get_actual_request_data(log_stream):
    boundary_pattern = r"(?<=boundary=)(.\w*)"
    content_length_pattern = r"(?<=Content-Length: )(.\d*)"

    boundary = ""
    actual_request_post = ""
    content_length = ""
    for log in log_stream:
        for log_arg in log:
            boundary_search = re.findall(boundary_pattern, log_arg)
            content_length_search = re.findall(content_length_pattern, log_arg)
            if boundary_search:
                boundary = boundary_search[0]
            if content_length_search:
                content_length = content_length_search[0]
            if "Content-Disposition" in log_arg or "\\x" in log_arg:
                # this will look like:
                #  b\'{content}\'
                # and escaped characters look like:
                #  \\r
                post_data = log_arg[2:-1]
                post_bytes = post_data.encode("utf-8")
                post_unescaped = post_bytes.decode("unicode_escape")
                actual_request_post = post_unescaped.encode("latin1")

    return boundary, content_length, actual_request_post


def test_post_file_as_data(  # pylint: disable=unused-argument
    requests, sock, log_stream, post_url, request_logging
):
    with open("tests/files/red_green.png", "rb") as file_1:
        python_requests.post(post_url, data=file_1, timeout=30)
        __, content_length, actual_request_post = get_actual_request_data(log_stream)

        requests.post("http://" + mocket.MOCK_HOST_1 + "/post", data=file_1)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Length"),
            mock.call(b": "),
            mock.call(content_length.encode()),
            mock.call(b"\r\n"),
        ]
    )
    sent = b"".join(sock.sent_data)
    assert sent.endswith(actual_request_post)


def test_post_files_text(  # pylint: disable=unused-argument
    sock, requests, log_stream, post_url, request_logging
):
    file_data = {
        "key_4": (None, "Value 5"),
    }

    python_requests.post(post_url, files=file_data, timeout=30)
    boundary, content_length, actual_request_post = get_actual_request_data(log_stream)

    requests._build_boundary_string = mock.Mock(return_value=boundary)
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(f"multipart/form-data; boundary={boundary}".encode()),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Length"),
            mock.call(b": "),
            mock.call(content_length.encode()),
            mock.call(b"\r\n"),
        ]
    )

    sent = b"".join(sock.sent_data)
    assert sent.endswith(actual_request_post)


def test_post_files_file(  # pylint: disable=unused-argument
    sock, requests, log_stream, post_url, request_logging
):
    with open("tests/files/red_green.png", "rb") as file_1:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
                {
                    "Key_1": "Value 1",
                    "Key_2": "Value 2",
                    "Key_3": "Value 3",
                },
            ),
        }

        python_requests.post(post_url, files=file_data, timeout=30)
        boundary, content_length, actual_request_post = get_actual_request_data(
            log_stream
        )

        requests._build_boundary_string = mock.Mock(return_value=boundary)
        requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(f"multipart/form-data; boundary={boundary}".encode()),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Length"),
            mock.call(b": "),
            mock.call(content_length.encode()),
            mock.call(b"\r\n"),
        ]
    )
    sent = b"".join(sock.sent_data)
    assert sent.endswith(actual_request_post)


def test_post_files_complex(  # pylint: disable=unused-argument
    sock, requests, log_stream, post_url, request_logging
):
    with open("tests/files/red_green.png", "rb") as file_1, open(
        "tests/files/green_red.png", "rb"
    ) as file_2:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
                {
                    "Key_1": "Value 1",
                    "Key_2": "Value 2",
                    "Key_3": "Value 3",
                },
            ),
            "key_4": (None, "Value 5"),
            "file_2": (
                "green_red.png",
                file_2,
                "image/png",
            ),
            "key_6": (None, "Value 6"),
        }

        python_requests.post(post_url, files=file_data, timeout=30)
        boundary, content_length, actual_request_post = get_actual_request_data(
            log_stream
        )

        requests._build_boundary_string = mock.Mock(return_value=boundary)
        requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(f"multipart/form-data; boundary={boundary}".encode()),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Length"),
            mock.call(b": "),
            mock.call(content_length.encode()),
            mock.call(b"\r\n"),
        ]
    )
    sent = b"".join(sock.sent_data)
    assert sent.endswith(actual_request_post)


def test_post_files_not_binary(requests):
    with open("tests/files/red_green.png", "r") as file_1:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
            ),
        }

        with pytest.raises(ValueError) as context:
            requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)
        assert "Files must be opened in binary mode" in str(context)
