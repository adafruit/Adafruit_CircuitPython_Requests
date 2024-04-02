# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Updated for Circuit Python 9.0
""" WiFi Simpletest """

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

print(f" | GET Text Test: {TEXT_URL}")
response = requests.get(TEXT_URL)
print(f" | ✅ GET Response: {response.text}")
response.close()
print(f" | ✂️ Disconnected from {TEXT_URL}")
print("-" * 80)

print(f" | GET Full Response Test: {JSON_GET_URL}")
response = requests.get(JSON_GET_URL)
print(f" | ✅ Unparsed Full JSON Response: {response.json()}")
response.close()
print(f" | ✂️ Disconnected from {JSON_GET_URL}")
print("-" * 80)

DATA = "This is an example of a JSON value"
print(f" | ✅ JSON 'value' POST Test: {JSON_POST_URL} {DATA}")
response = requests.post(JSON_POST_URL, data=DATA)
json_resp = response.json()
# Parse out the 'data' key from json_resp dict.
print(f" | ✅ JSON 'value' Response: {json_resp['data']}")
response.close()
print(f" | ✂️ Disconnected from {JSON_POST_URL}")
print("-" * 80)

json_data = {"Date": "January 1, 1970"}
print(f" | ✅ JSON 'key':'value' POST Test: {JSON_POST_URL} {json_data}")
response = requests.post(JSON_POST_URL, json=json_data)
json_resp = response.json()
# Parse out the 'json' key from json_resp dict.
print(f" | ✅ JSON 'key':'value' Response: {json_resp['json']}")
response.close()
print(f" | ✂️ Disconnected from {JSON_POST_URL}")
print("-" * 80)

print("Finished!")
