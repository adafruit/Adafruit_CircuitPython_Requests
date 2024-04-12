# SPDX-FileCopyrightText: 2024 DJDevon3
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0
""" WiFi Context Manager Basics Example """

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
print("✅ Wifi!\n")

print("-" * 40)

# This method requires an explicit close
print("Explicit Close() Example")
response = requests.get(JSON_GET_URL)
print(" | ✅ Connected to JSON")

json_data = response.json()
if response.status_code == 200:
    print(f" | 🆗 Status Code: {response.status_code}")
else:
    print(f" |  | Status Code: {response.status_code}")
headers = json_data["headers"]
date = response.headers.get("date", "")
print(f" |  | Response Timestamp: {date}")

# Close response manually (prone to mid-disconnect socket errors, out of retries)
response.close()
print(f" | ✂️ Disconnected from {JSON_GET_URL}")
print("-" * 40)

print("versus")

print("-" * 40)

# Closing response is included automatically using "with"
print("Context Manager WITH Example")
response = requests.get(JSON_GET_URL)
print(" | ✅ Connected to JSON")

# Wrap a request using a with statement
with requests.get(JSON_GET_URL) as response:
    date = response.headers.get("date", "")
    json_data = response.json()
    if response.status_code == 200:
        print(f" | 🆗 Status Code: {response.status_code}")
    else:
        print(f" |  | Status Code: {response.status_code}")
    headers = json_data["headers"]
    print(f" |  | Response Timestamp: {date}")

# Notice there is no response.close() here
# It's handled automatically in a with statement
# This is the better way.
print(f" | ✂️ Disconnected from {JSON_GET_URL}")

print("-" * 40)

print("\nBoth examples are functionally identical")
print(
    "However, a with statement is more robust against disconnections mid-request "
    + "and automatically closes the response."
)
print("Using with statements for requests is recommended\n\n")
