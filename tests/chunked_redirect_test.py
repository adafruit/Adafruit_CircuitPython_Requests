# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Redirection Tests """

from unittest import mock

import mocket
from chunk_test import _chunk

import adafruit_requests

IP = "1.2.3.4"
HOST = "docs.google.com"
PATH_BASE = (
    "/spreadsheets/d/e/2PACX-1vR1WjUKz35-ek6SiR5droDfvPp51MTds4wUs57vEZNh2uDfihSTPhTaiiRo"
    "vLbNe1mkeRgurppRJ_Zy/"
)
PATH = PATH_BASE + "pub?output=tsv"

FILE_REDIRECT = (
    b"e@2PACX-1vR1WjUKz35-ek6SiR5droDfvPp51MTds4wUs57vEZNh2uDfihSTPhTai"
    b"iRovLbNe1mkeRgurppRJ_Zy?output=tsv"
)
RELATIVE_RELATIVE_REDIRECT = (
    b"370cmver1f290kjsnpar5ku2h9g/3llvt5u8njbvat22m9l19db1h4/1656191325000/109226138307867586192/*/"
    + FILE_REDIRECT
)
RELATIVE_ABSOLUTE_REDIRECT = (
    b"/pub/70cmver1f290kjsnpar5ku2h9g/" + RELATIVE_RELATIVE_REDIRECT
)
ABSOLUTE_ABSOLUTE_REDIRECT = (
    b"https://doc-14-2g-sheets.googleusercontent.com" + RELATIVE_ABSOLUTE_REDIRECT
)

# response headers returned from the initial request
HEADERS_REDIRECT = (
    b"HTTP/1.1 307 Temporary Redirect\r\n"
    b"Content-Type: text/html; charset=UTF-8\r\n"
    b"Cache-Control: no-cache, no-store, max-age=0, must-revalidate\r\n"
    b"Pragma: no-cache\r\n"
    b"Expires: Mon, 01 Jan 1990 00:00:00 GMT\r\n"
    b"Date: Sat, 25 Jun 2022 21:08:48 GMT\r\n"
    b"Location: NEW_LOCATION_HERE\r\n"
    b'P3P: CP="This is not a P3P policy! See g.co/p3phelp for more info."\r\n'
    b"X-Content-Type-Options: nosniff\r\n"
    b"X-XSS-Protection: 1; mode=block\r\n"
    b"Server: GSE\r\n"
    b"Set-Cookie: NID=511=EcnO010Porg0NIrxM8tSG6MhfQiVtWrQS42CjhKEpzwIvzBj2PFYH0-H_N--EAXaPBkR2j"
    b"FjAWEAxIJNqhvKb0vswOWp9hqcCrO51S8kO5I4C3"
    b"Is2ctWe1b_ysRU-6hjnJyLHzqjXotAWzEmr_qA3bpqWDwlRaQIiC6SvxM8L0M; expires=Sun, 25-Dec-2022 "
    b"21:08:48 GMT; path=/; "
    b"domain=.google.com; HttpOnly\r\n"
    b'Alt-Svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; '
    b'ma=2592000,h3-Q046=":443";'
    b' ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"\r\n'
    b"Accept-Ranges: none\r\n"
    b"Vary: Accept-Encoding\r\n"
    b"Transfer-Encoding: chunked\r\n\r\n"
)

# response body returned from the initial request (needs to be chunked.)
BODY_REDIRECT = (
    b"<HTML>\n<HEAD>\n<TITLE>Temporary Redirect</TITLE>\n</HEAD>\n"
    b'<BODY BGCOLOR="#FFFFFF" TEXT="#000000">\n'
    b"<H1>Temporary Redirect</H1>\nThe document has moved "
    b'<A HREF="https://doc-14-2g-sheets.googleusercontent.com/pub'
    b"/70cmver1f290kjsnpar5ku2h9g/3llvt5u8njbvat22m9l19db1h4/1656191325000"
    b"/109226138307867586192/*/e@2PACX-1vR1WjUKz35-"
    b"ek6SiR5droDfvPp51MTds4wUs57vEZNh2uDfihSTPhTaiiRovLbNe1mkeRgurppRJ_Zy?"
    b'output=tsv">here</A>.\n</BODY>\n</HTML>\n'
)

# response headers from the request to the redirected location
HEADERS = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: text/tab-separated-values\r\n"
    b"X-Frame-Options: ALLOW-FROM https://docs.google.com\r\n"
    b"X-Robots-Tag: noindex, nofollow, nosnippet\r\n"
    b"Expires: Sat, 25 Jun 2022 21:08:49 GMT\r\n"
    b"Date: Sat, 25 Jun 2022 21:08:49 GMT\r\n"
    b"Cache-Control: private, max-age=300\r\n"
    b'Content-Disposition: attachment; filename="WeeklyPlanner-Sheet1.tsv"; '
    b"filename*=UTF-8''Weekly%20Planner%20-%20Sheet1.tsv\r\n"
    b"Access-Control-Allow-Origin: *\r\n"
    b"Access-Control-Expose-Headers: Cache-Control,Content-Disposition,Content-Encoding,"
    b"Content-Length,Content-Type,Date,Expires,Server,Transfer-Encoding\r\n"
    b"Content-Security-Policy: frame-ancestors 'self' https://docs.google.com\r\n"
    b"Content-Security-Policy: base-uri 'self';object-src 'self';report-uri https://"
    b"doc-14-2g-sheets.googleusercontent.com/spreadsheets/cspreport;"
    b"script-src 'report-sample' 'nonce-6V57medLoq3hw2BWeyGu_A' 'unsafe-inline' 'strict-dynamic'"
    b" https: http: 'unsafe-eval';worker-src 'self' blob:\r\n"
    b"X-Content-Type-Options: nosniff\r\n"
    b"X-XSS-Protection: 1; mode=block\r\n"
    b"Server: GSE\r\n"
    b'Alt-Svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; '
    b'ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443";'
    b' ma=2592000,quic=":443"; ma=2592000; v="46,43"\r\n'
    b"Accept-Ranges: none\r\n"
    b"Vary: Accept-Encoding\r\n"
    b"Transfer-Encoding: chunked\r\n\r\n"
)

# response body from the request to the redirected location (needs to be chunked.)
BODY = (
    b"Sunday\tMonday\tTuesday\tWednesday\tThursday\tFriday\tSaturday\r\n"
    b"Rest\tSpin class\tRowing\tWerewolf Twitter\tWeights\tLaundry\tPoke bowl\r\n"
    b"\t\tZoom call\tShow & Tell\t\tMow lawn\tSynth Riders\r\n"
    b"\t\tTacos\tAsk an Engineer\t\tTrash pickup\t\r\n"
    b"\t\t\t\t\tLeg day\t\r\n"
    b"\t\t\t\t\tPizza night\t"
)


class MocketRecvInto(mocket.Mocket):  # pylint: disable=too-few-public-methods
    """A special Mocket to cap the number of bytes returned from recv_into()"""

    def __init__(self, response):
        super().__init__(response)
        self.recv_into = mock.Mock(side_effect=self._recv_into)

    def _recv_into(self, buf, nbytes=0):
        assert isinstance(nbytes, int) and nbytes >= 0
        read = nbytes if nbytes > 0 else len(buf)
        remaining = len(self._response) - self._position
        read = min(read, remaining, 205)
        end = self._position + read
        buf[:read] = self._response[self._position : end]
        self._position = end
        return read


def test_chunked_absolute_absolute_redirect():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 443)),)
    chunk = _chunk(BODY_REDIRECT, len(BODY_REDIRECT))
    chunk2 = _chunk(BODY, len(BODY))

    redirect = HEADERS_REDIRECT.replace(
        b"NEW_LOCATION_HERE", ABSOLUTE_ABSOLUTE_REDIRECT
    )
    sock1 = MocketRecvInto(redirect + chunk)
    sock2 = mocket.Mocket(HEADERS + chunk2)
    pool.socket.side_effect = (sock1, sock2)

    requests_session = adafruit_requests.Session(pool, mocket.SSLContext())
    response = requests_session.get("https://" + HOST + PATH)

    sock1.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with(
        ("doc-14-2g-sheets.googleusercontent.com", 443)
    )
    sock2.send.assert_has_calls([mock.call(RELATIVE_ABSOLUTE_REDIRECT[1:])])

    assert response.text == str(BODY, "utf-8")


def test_chunked_relative_absolute_redirect():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 443)),)
    chunk = _chunk(BODY_REDIRECT, len(BODY_REDIRECT))
    chunk2 = _chunk(BODY, len(BODY))

    redirect = HEADERS_REDIRECT.replace(
        b"NEW_LOCATION_HERE", RELATIVE_ABSOLUTE_REDIRECT
    )
    sock1 = MocketRecvInto(redirect + chunk)
    sock2 = mocket.Mocket(HEADERS + chunk2)
    pool.socket.side_effect = (sock1, sock2)

    requests_session = adafruit_requests.Session(pool, mocket.SSLContext())
    response = requests_session.get("https://" + HOST + PATH)

    sock1.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with(("docs.google.com", 443))
    sock2.send.assert_has_calls([mock.call(RELATIVE_ABSOLUTE_REDIRECT[1:])])

    assert response.text == str(BODY, "utf-8")


def test_chunked_relative_relative_redirect():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 443)),)
    chunk = _chunk(BODY_REDIRECT, len(BODY_REDIRECT))
    chunk2 = _chunk(BODY, len(BODY))

    redirect = HEADERS_REDIRECT.replace(
        b"NEW_LOCATION_HERE", RELATIVE_RELATIVE_REDIRECT
    )
    sock1 = MocketRecvInto(redirect + chunk)
    sock2 = mocket.Mocket(HEADERS + chunk2)
    pool.socket.side_effect = (sock1, sock2)

    requests_session = adafruit_requests.Session(pool, mocket.SSLContext())
    response = requests_session.get("https://" + HOST + PATH)

    sock1.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with(("docs.google.com", 443))
    sock2.send.assert_has_calls(
        [mock.call(bytes(PATH_BASE[1:], "utf-8") + RELATIVE_RELATIVE_REDIRECT)]
    )

    assert response.text == str(BODY, "utf-8")


def test_chunked_relative_relative_redirect_backstep():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 443)),)
    chunk = _chunk(BODY_REDIRECT, len(BODY_REDIRECT))
    chunk2 = _chunk(BODY, len(BODY))

    remove_paths = 2
    backstep = b"../" * remove_paths
    path_base_parts = PATH_BASE.split("/")
    # PATH_BASE starts with "/" so skip it and also remove from the count
    path_base = (
        "/".join(path_base_parts[1 : len(path_base_parts) - remove_paths - 1]) + "/"
    )

    redirect = HEADERS_REDIRECT.replace(
        b"NEW_LOCATION_HERE", backstep + RELATIVE_RELATIVE_REDIRECT
    )
    sock1 = MocketRecvInto(redirect + chunk)
    sock2 = mocket.Mocket(HEADERS + chunk2)
    pool.socket.side_effect = (sock1, sock2)

    requests_session = adafruit_requests.Session(pool, mocket.SSLContext())
    response = requests_session.get("https://" + HOST + PATH)

    sock1.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with(("docs.google.com", 443))
    sock2.send.assert_has_calls(
        [mock.call(bytes(path_base, "utf-8") + RELATIVE_RELATIVE_REDIRECT)]
    )

    assert response.text == str(BODY, "utf-8")


def test_chunked_allow_redirects_false():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 443)),)
    chunk = _chunk(BODY_REDIRECT, len(BODY_REDIRECT))
    chunk2 = _chunk(BODY, len(BODY))

    redirect = HEADERS_REDIRECT.replace(
        b"NEW_LOCATION_HERE", ABSOLUTE_ABSOLUTE_REDIRECT
    )
    sock1 = MocketRecvInto(redirect + chunk)
    sock2 = mocket.Mocket(HEADERS + chunk2)
    pool.socket.side_effect = (sock1, sock2)

    requests_session = adafruit_requests.Session(pool, mocket.SSLContext())
    response = requests_session.get("https://" + HOST + PATH, allow_redirects=False)

    sock1.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_not_called()

    assert response.text == str(BODY_REDIRECT, "utf-8")
