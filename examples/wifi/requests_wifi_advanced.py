# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0
""" WiFi Advanced (User-Agent & Status Codes) Example """
# pylint: disable=import-error

import os

import adafruit_connection_manager
import wifi

import adafruit_requests

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

JSON_GET_URL = "https://httpbin.org/get"
STATUS_TEST = "https://httpbin.org/status/"

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi


def print_http_status(code, description):
    """Returns HTTP status code and description"""
    if "100" <= code <= "103":
        print(f" | ✅ Status Test: {code} - {description}")
    elif "200" <= code <= "299":
        print(f" | ✅ Status Test: {code} - {description}")
    elif "300" <= code <= "600":
        print(f" | ❌ Status Test: {code} - {description}")
    else:
        print(f" | Unknown Response Status: {code} - {description}")


# All HTTP Status Codes
http_status_codes = {
    "100": "Continue",
    "101": "Switching Protocols",
    "102": "Processing",
    "103": "Early Hints",
    "200": "OK",
    "201": "Created",
    "202": "Accepted",
    "203": "Non-Authoritative Information",
    "204": "No Content",
    "205": "Reset Content",
    "206": "Partial Content",
    "207": "Multi-Status",
    "208": "Already Reported",
    "226": "IM Used",
    "300": "Multiple Choices",
    "301": "Moved Permanently",
    "302": "Found",
    "303": "See Other",
    "304": "Not Modified",
    "305": "Use Proxy",
    "306": "Unused",
    "307": "Temporary Redirect",
    "308": "Permanent Redirect",
    "400": "Bad Request",
    "401": "Unauthorized",
    "402": "Payment Required",
    "403": "Forbidden",
    "404": "Not Found",
    "405": "Method Not Allowed",
    "406": "Not Acceptable",
    "407": "Proxy Authentication Required",
    "408": "Request Timeout",
    "409": "Conflict",
    "410": "Gone",
    "411": "Length Required",
    "412": "Precondition Failed",
    "413": "Payload Too Large",
    "414": "URI Too Long",
    "415": "Unsupported Media Type",
    "416": "Range Not Satisfiable",
    "417": "Expectation Failed",
    "418": "I'm a teapot",
    "421": "Misdirected Request",
    "422": "Unprocessable Entity",
    "423": "Locked",
    "424": "Failed Dependency",
    "425": "Too Early",
    "426": "Upgrade Required",
    "428": "Precondition Required",
    "429": "Too Many Requests",
    "431": "Request Header Fields Too Large",
    "451": "Unavailable For Legal Reasons",
    "500": "Internal Server Error",
    "501": "Not Implemented",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
    "504": "Gateway Timeout",
    "505": "HTTP Version Not Supported",
    "506": "Variant Also Negotiates",
    "507": "Insufficient Storage",
    "508": "Loop Detected",
    "510": "Not Extended",
    "511": "Network Authentication Required",
}


print(f"\nConnecting to {ssid}...")
print(f"Signal Strength: {rssi}")
try:
    # Connect to the Wi-Fi network
    wifi.radio.connect(ssid, password)
except OSError as e:
    print(f"❌ OSError: {e}")
print("✅ Wifi!")

JSON_GET_URL = "https://httpbin.org/get"

# Define a custom header as a dict.
HEADERS = {"user-agent": "blinka/1.0.0"}

print(f" | GET JSON: {JSON_GET_URL}")
response = requests.get(JSON_GET_URL, headers=HEADERS)

json_data = response.json()
HEADERS = json_data["headers"]
print(f" | User-Agent: {HEADERS['User-Agent']}")

# HTTP STATUS CODE TESTING
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
STATUS_CODE = str(response.status_code)
STATUS_DESCRIPTION = http_status_codes.get(STATUS_CODE, "Unknown Status Code")
print_http_status(STATUS_CODE, STATUS_DESCRIPTION)
response.close()
print(f" | ✂️ Disconnected from {JSON_GET_URL}")
print(" | ")
print(f" | Status Code Test: {JSON_GET_URL}")

# Some return errors then confirm the error (that's a good thing)
# Demonstrates not all errors have the same behavior
# 300, 304, and 306 in particular
for codes in sorted(http_status_codes.keys(), key=int):
    status_test_url = STATUS_TEST + codes
    response = requests.get(status_test_url, headers=HEADERS)
    SORT_STATUS_CODE = str(response.status_code)
    SORT_STATUS_DESC = http_status_codes.get(SORT_STATUS_CODE, "Unknown Status Code")
    print_http_status(SORT_STATUS_CODE, SORT_STATUS_DESC)
    response.close()

print(f" | ✂️ Disconnected from {JSON_GET_URL}")

print("Finished!")
