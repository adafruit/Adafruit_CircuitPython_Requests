# SPDX-FileCopyrightText: 2024 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 9.x
"""Queue-Times.com API Example"""

import os
import time

import adafruit_connection_manager
import wifi

import adafruit_requests

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
SLEEP_TIME = 300

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Publicly Open API (no credentials required)
QTIMES_SOURCE = "https://queue-times.com/parks/16/queue_times.json"


def time_calc(input_time):
    """Converts seconds to minutes/hours/days"""
    if input_time < 60:
        return f"{input_time:.0f} seconds"
    if input_time < 3600:
        return f"{input_time / 60:.0f} minutes"
    if input_time < 86400:
        return f"{input_time / 60 / 60:.0f} hours"
    return f"{input_time / 60 / 60 / 24:.1f} days"


qtimes_json = {}
while True:
    now = time.monotonic()
    # Connect to Wi-Fi
    print("\n===============================")
    print("Connecting to WiFi...")
    while not wifi.radio.ipv4_address:
        try:
            wifi.radio.connect(ssid, password)
        except ConnectionError as e:
            print("❌ Connection Error:", e)
            print("Retrying in 10 seconds")
    print("✅ WiFi!")

    try:
        print(" | Attempting to GET Queue-Times JSON!")
        try:
            qtimes_response = requests.get(url=QTIMES_SOURCE)
            qtimes_json = qtimes_response.json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
        print(" | ✅ Queue-Times JSON!")

        DEBUG_QTIMES = False
        if DEBUG_QTIMES:
            print("Full API GET URL: ", QTIMES_SOURCE)
            print(qtimes_json)
        qtimes_response.close()
        print("✂️ Disconnected from Queue-Times API")

        print("\nFinished!")
        print(f"Board Uptime: {time_calc(time.monotonic())}")
        print(f"Next Update: {time_calc(SLEEP_TIME)}")
        print("===============================")
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        break

    # Loop infinitely until its time to re-poll
    if time.monotonic() - now <= SLEEP_TIME:
        for land in qtimes_json["lands"]:
            qtimes_lands = str(land["name"])
            print(f" |  | Lands: {qtimes_lands}")
            time.sleep(1)

            # Loop through each ride in the land
            for ride in land["rides"]:
                qtimes_rides = str(ride["name"])
                qtimes_queuetime = str(ride["wait_time"])
                qtimes_isopen = str(ride["is_open"])

                print(f" |  | Ride: {qtimes_rides}")
                print(f" |  | Queue Time: {qtimes_queuetime} Minutes")
                if qtimes_isopen == "False":
                    print(" |  | Status: Closed")
                elif qtimes_isopen == "True":
                    print(" |  | Status: Open")
                else:
                    print(" |  | Status: Unknown")

                time.sleep(1)  # delay between list items
    else:  # When its time to poll, break to top of while True loop.
        break
