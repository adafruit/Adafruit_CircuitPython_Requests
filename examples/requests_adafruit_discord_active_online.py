# SPDX-FileCopyrightText: 2022 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Adafruit_Discord_Active_Users_Example"""
#  pylint: disable=line-too-long
import gc
import re
import time
import ssl
import wifi
import json
import socketpool
import adafruit_requests

# No user or token required, web scrape.

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

# https://img.shields.io/discord/327254708534116352.svg
ADA_DISCORD_SVG = (
    "https://img.shields.io/discord/327254708534116352.json"
)

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(secrets['ssid'], secrets['password'])
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
    gc.collect()
print("Connected!\n")

while True:
    try:
        print("\nAttempting to GET DISCORD SVG!")  # --------------------------------
        # Print Request to Serial
        debug_request = True  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", ADA_DISCORD_SVG)
        print("===============================")
        try:
            ada_SVG_response = requests.get(ADA_DISCORD_SVG).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
            
        # Print Full JSON to Serial
        full_ada_SVG_json_response = True # Change to true to see full response
        if full_ada_SVG_json_response:
            ada_SVG_dump_object = json.dumps(ada_SVG_response)
            print("JSON Dump: ", ada_SVG_dump_object)
            
        # Print Debugging to Serial
        ada_SVG_debug = True # Set to True to print Serial data
        if ada_SVG_debug:
            ada_SVG_users = ada_SVG_response['value']
            print("SVG Value: ", ada_SVG_users)
            regex = " online"
            replace_with_nothing = ""
            regex_users = re.sub(regex, replace_with_nothing, ada_SVG_users)
            print("Regex Value: ", regex_users)
        print("Monotonic: ", time.monotonic())

        print("\nFinished!")
        print("Next Update in %s %s" % (int(sleep_int), sleep_time_conversion))
        print("===============================")
        gc.collect()
    # pylint: disable=broad-except
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
