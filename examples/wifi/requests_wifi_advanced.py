# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0

""" WiFi Advanced Example """

import os

import adafruit_connection_manager
import wifi

import adafruit_requests

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi

JSON_GET_URL = "https://httpbin.org/get"

print(f"\nConnecting to {ssid}...")
print(f"Signal Strength: {rssi}")
try:
    # Connect to the Wi-Fi network
    wifi.radio.connect(ssid, password)
except OSError as e:
    print(f"❌ OSError: {e}")
print("✅ Wifi!")

# Define a custom header as a dict.
headers = {"user-agent": "blinka/1.0.0"}
print(f" | Fetching JSON: {JSON_GET_URL}")

# GET JSON
response = requests.get(JSON_GET_URL, headers=headers)
content_type = response.headers.get("content-type", "")
date = response.headers.get("date", "")

json_data = response.json()
headers = json_data["headers"]

# JSON Response
if response.status_code == 200:
    print(f" | 🆗 Status Code: {response.status_code}")
else:
    print(f" |  | Status Code: {response.status_code}")
print(f" | ✅ Custom User-Agent Header: {headers['User-Agent']}")
print(f" | ✅ Content-Type: {content_type}")
print(f" | ✅ Response Timestamp: {date}")

# Close, delete and collect the response data
response.close()

print(f" | ✂️ Disconnected from {JSON_GET_URL}")
