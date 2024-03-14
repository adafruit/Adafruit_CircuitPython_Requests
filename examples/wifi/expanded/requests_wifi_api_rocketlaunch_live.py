# SPDX-FileCopyrightText: 2024 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.2.x
"""RocketLaunch.Live API Example"""

import gc
import os
import ssl
import time

import socketpool
import wifi

import adafruit_requests

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

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


# Free Public API, no token or header required
ROCKETLAUNCH_SOURCE = "https://fdo.rocketlaunch.live/json/launches/next/1"

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(ssid, password)
    except ConnectionError as e:
        print("❌ Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
    gc.collect()
print("✅ WiFi!")
print("===============================")

while True:
    try:
        # Print Request to Serial
        print("Attempting to GET RocketLaunch.Live JSON!")
        debug_rocketlaunch_full_response = False

        rocketlaunch_response = requests.get(url=ROCKETLAUNCH_SOURCE)
        try:
            rocketlaunch_json = rocketlaunch_response.json()
        except ConnectionError as e:
            print("❌ Connection Error:", e)
            print("Retrying in 10 seconds")
        if debug_rocketlaunch_full_response:
            print("Full API GET URL: ", ROCKETLAUNCH_SOURCE)
            print(rocketlaunch_json)

        print("✅ RocketLaunch.Live JSON!")
        rocketlaunch_flightname = str(rocketlaunch_json["result"][0]["name"])
        print(f" | Flight Name: {rocketlaunch_flightname}")
        rocketlaunch_provider = str(rocketlaunch_json["result"][0]["provider"]["name"])
        print(f" | Provider: {rocketlaunch_provider}")
        rocketlaunch_vehiclename = str(
            rocketlaunch_json["result"][0]["vehicle"]["name"]
        )
        print(f" | Vehicle Name: {rocketlaunch_vehiclename}")

        rocketlaunch_winopen = str(rocketlaunch_json["result"][0]["win_open"])
        rocketlaunch_winclose = str(rocketlaunch_json["result"][0]["win_close"])
        print(f" | Window: {rocketlaunch_winopen} to {rocketlaunch_winclose}")

        rocketlaunch_sitename = str(
            rocketlaunch_json["result"][0]["pad"]["location"]["name"]
        )
        print(f" | Launch Site: {rocketlaunch_sitename}")

        rocketlaunch_mission = str(
            rocketlaunch_json["result"][0]["mission_description"]
        )
        if rocketlaunch_mission != "None":
            print(f" | Mission: {rocketlaunch_mission}")

        print("\nFinished!")
        print("Board Uptime: ", time.monotonic())
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")
        gc.collect()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
