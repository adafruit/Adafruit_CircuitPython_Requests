# SPDX-FileCopyrightText: 2024 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 9.x
"""Adafruit Services Status Example"""

import os
import time

import adafruit_connection_manager
import wifi

import adafruit_requests

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
SSL_CONTEXT = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, SSL_CONTEXT)

# Use settings.toml for credentials
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Adafruit uses https://uptimerobot.com/api/ for Service Monitoring
# Public API, no credentials required
SOURCE = "https://www.adafruitstatus.com/api/getMonitorList/B9pLZuVj2w"
HEADER = {"user-agent": "blinka/1.0.0"}

while True:
    # Connect to Wi-Fi
    print("\nConnecting to WiFi...")
    while not wifi.radio.connected:
        try:
            wifi.radio.connect(ssid, password)
        except ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            time.sleep(60)
    print("📡 Wifi!")

    while wifi.radio.connected:
        try:
            try:
                with requests.get(url=SOURCE, headers=HEADER) as response:
                    response_json = response.json()
            # Request error catcher. If script fails during request.
            except (OSError, KeyError) as e:
                if e.errno == -2:
                    print(f"❌ gaierror (DNS failure), waiting to hard reset {e}")
                    time.sleep(240)
                    microcontroller.reset()
                print(f"❌ Key Error: {e}")
                time.sleep(60)

            # Server Header Responses
            response_headers = response.headers
            # print(f"Response Headers: {response_headers}")
            print("\nHeaders:")
            header_date = response.headers["date"]
            print(f"Request Timestamp: {header_date}")
            header_rate_limit = response.headers["x-ratelimit-remaining"]
            print(f"Rate Limit Remaining: {header_rate_limit}")
            header_content_type = response.headers["content-type"]
            print(f"Content Type: {header_content_type}")

            # Server JSON Content Responses
            print("\nJSON: ")
            json_status = response_json["status"]
            print(f"Response Status: {json_status}")
            json_psp_monitors = response_json["psp"]["totalMonitors"]
            print(f"Total Monitors: {json_psp_monitors}")

            for i in response_json["psp"]["monitors"]:
                monitors = str(i["name"])
                if i["statusClass"] == "success":
                    print(f" ✅ Monitor: {monitors}")
                else:
                    print(f" ❌ Monitor: {monitors}")

        # General error catcher. If script fails after a successful request.
        except (OSError, ValueError, RuntimeError) as e:
            print(f"❌ General Exception Error: {e}")
            time.sleep(60)
            break  # breaks to while True to re-check WiFi status
        time.sleep(300)  # If everything succeeds, time until next poll update
