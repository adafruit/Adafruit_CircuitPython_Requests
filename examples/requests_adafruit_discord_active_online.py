# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
"""
Coded for Circuit Python 8.2.3
requests_adafruit_discord_active_online
"""
import gc
import os
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Public API. No user or token required
# JSON web scrape from SHIELDS.IO
# Adafruit uses Shields.IO to see online users

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Time in seconds between updates (polling)
# 600 = 10 mins, 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900

# this example uses settings.toml for credentials
ssid = os.getenv("WIFI_SSID")
appw = os.getenv("WIFI_PASSWORD")


# Converts seconds to minutes/hours/days
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
    else:
        sleep_int = input_time / 60 / 60 / 24
        time_output = f"{sleep_int:.1f} days"
    return time_output


# Originally attempted to use SVG. Found JSON exists with same filename.
# https://img.shields.io/discord/327254708534116352.svg
ADA_DISCORD_JSON = "https://img.shields.io/discord/327254708534116352.json"

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(ssid, appw)
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
    gc.collect()
print("Connected!\n")

while True:
    try:
        print(
            "\nAttempting to GET DISCORD SHIELD JSON!"
        )  # --------------------------------
        # Print Request to Serial
        debug_request = True  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", ADA_DISCORD_JSON)
        print("===============================")
        try:
            ada_response = requests.get(ADA_DISCORD_JSON).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Full JSON to Serial
        full_ada_json_response = True  # Change to true to see full response
        if full_ada_json_response:
            ada_dump_object = json.dumps(ada_response)
            print("JSON Dump: ", ada_dump_object)

        # Print Debugging to Serial
        ada_debug = True  # Set to True to print Serial data
        if ada_debug:
            ada_users = ada_response["value"]
            print("JSON Value: ", ada_users)
            online_string = " online"
            replace_with_nothing = ""
            string_replace_users = ada_users.replace(
                online_string, replace_with_nothing
            )
            print("Replaced Value: ", string_replace_users)
        print("Monotonic: ", time.monotonic())

        print("\nFinished!")
        print("Next Update: ", time_calc(sleep_time))
        print("===============================")
        gc.collect()

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
