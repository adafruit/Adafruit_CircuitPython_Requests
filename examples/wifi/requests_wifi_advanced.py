# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0
""" WiFi Advanced Example """
# pylint: disable=import-error

import os

import adafruit_connection_manager
import wifi

import adafruit_requests

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "https://httpbin.org/get"
JSON_POST_URL = "https://httpbin.org/post"

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi

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
headers = {"user-agent": "blinka/1.0.0"}

print(f" | Fetching JSON: {JSON_GET_URL}")
response = requests.get(JSON_GET_URL, headers=headers)

json_data = response.json()
headers = json_data["headers"]
print(f" | ✅ Response Custom User-Agent Header: {headers['User-Agent']}")

# Read Response's HTTP status code
print(f" | ✅ Response HTTP Status Code: {response.status_code}")

# Close, delete and collect the response data
response.close()
print(f" | ✂️ Disconnected from {JSON_GET_URL}")
print("Finished!")
