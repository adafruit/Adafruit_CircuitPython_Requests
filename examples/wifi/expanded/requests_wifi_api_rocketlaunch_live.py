# SPDX-FileCopyrightText: 2024 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.2.x
"""RocketLaunch.Live API Example"""

import os
import time

import adafruit_connection_manager
import wifi

import adafruit_requests

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 43200

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("WIFI_SSID")
password = os.getenv("WIFI_PASSWORD")


# Converts seconds in minutes/hours/days
def time_calc(input_time):
    if input_time < 60:
        sleep_int = input_time
        time_output = f"{sleep_int:.0f} seconds"
    elif 60 <= input_time < 3600:
        sleep_int = input_time / 60
        time_output = f"{sleep_int:.0f} minutes"
    elif 3600 <= input_time < 86400:
        sleep_int = input_time / 60 / 60
        time_output = f"{sleep_int:.0f} hours"
    elif 86400 <= input_time < 432000:
        sleep_int = input_time / 60 / 60 / 24
        time_output = f"{sleep_int:.1f} days"
    else:  # if > 5 days convert float to int & display whole days
        sleep_int = input_time / 60 / 60 / 24
        time_output = f"{sleep_int:.0f} days"
    return time_output


# Publicly available data no header required
# The number at the end is the amount of launches (max 5 free api)
ROCKETLAUNCH_SOURCE = "https://fdo.rocketlaunch.live/json/launches/next/1"

# Initalize Wifi, Socket Pool, Request Session
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

while True:
    # Connect to Wi-Fi
    print("\n===============================")
    print("Connecting to WiFi...")
    while not wifi.radio.ipv4_address:
        try:
            wifi.radio.connect(ssid, password)
        except ConnectionError as e:
            print("❌ Connection Error:", e)
            print("Retrying in 10 seconds")
    print("✅ Wifi!")
    try:
        # Print Request to Serial
        print(" | Attempting to GET RocketLaunch.Live JSON!")
        time.sleep(2)
        debug_rocketlaunch_full_response = False

        try:
            rocketlaunch_response = requests.get(url=ROCKETLAUNCH_SOURCE)
            rocketlaunch_json = rocketlaunch_response.json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
        print(" | ✅ RocketLaunch.Live JSON!")

        if debug_rocketlaunch_full_response:
            print("Full API GET URL: ", ROCKETLAUNCH_SOURCE)
            print(rocketlaunch_json)

        # JSON Endpoints
        RLFN = str(rocketlaunch_json["result"][0]["name"])
        RLWO = str(rocketlaunch_json["result"][0]["win_open"])
        TMINUS = str(rocketlaunch_json["result"][0]["t0"])
        RLWC = str(rocketlaunch_json["result"][0]["win_close"])
        RLP = str(rocketlaunch_json["result"][0]["provider"]["name"])
        RLVN = str(rocketlaunch_json["result"][0]["vehicle"]["name"])
        RLPN = str(rocketlaunch_json["result"][0]["pad"]["name"])
        RLLS = str(rocketlaunch_json["result"][0]["pad"]["location"]["name"])
        RLLD = str(rocketlaunch_json["result"][0]["launch_description"])
        RLM = str(rocketlaunch_json["result"][0]["mission_description"])
        RLDATE = str(rocketlaunch_json["result"][0]["date_str"])

        # Print to serial & display label if endpoint not "None"
        if RLDATE != "None":
            print(f" |  | Date: {RLDATE}")
        if RLFN != "None":
            print(f" |  | Flight: {RLFN}")
        if RLP != "None":
            print(f" |  | Provider: {RLP}")
        if RLVN != "None":
            print(f" |  | Vehicle: {RLVN}")
        if RLWO != "None":
            print(f" |  | Window: {RLWO} to {RLWC}")
        elif TMINUS != "None":
            print(f" |  | Window: {TMINUS} to {RLWC}")
        if RLLS != "None":
            print(f" |  | Site: {RLLS}")
        if RLPN != "None":
            print(f" |  | Pad: {RLPN}")
        if RLLD != "None":
            print(f" |  | Description: {RLLD}")
        if RLM != "None":
            print(f" |  | Mission: {RLM}")

        print("\nFinished!")
        print("Board Uptime: ", time.monotonic())
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        break
    time.sleep(sleep_time)
