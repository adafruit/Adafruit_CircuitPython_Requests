# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Adafruit_Discord_Active_Users_Example"""
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# No user or token required, 100% JSON web scrape from SHIELDS.IO
# Adafruit uses Shields.IO to see online users

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900

try:
    from secrets import secrets
except ImportError:
    print("Secrets File Import Error")
    raise

if sleep_time < 60:
    sleep_time_conversion = "seconds"
    sleep_int = sleep_time
elif 60 <= sleep_time < 3600:
    sleep_int = sleep_time / 60
    sleep_time_conversion = "minutes"
elif 3600 <= sleep_time < 86400:
    sleep_int = sleep_time / 60 / 60
    sleep_time_conversion = "hours"
else:
    sleep_int = sleep_time / 60 / 60 / 24
    sleep_time_conversion = "days"

# Originally attempted to use SVG. Found JSON exists with same filename.
# https://img.shields.io/discord/327254708534116352.svg
ADA_DISCORD_JSON = "https://img.shields.io/discord/327254708534116352.json"

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(secrets["ssid"], secrets["password"])
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
        print("Next Update in %s %s" % (int(sleep_int), sleep_time_conversion))
        print("===============================")
        gc.collect()

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
