# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Github_API_Example"""
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Github developer token required.
# Ensure these are uncommented and in secrets.py or .env
# "Github_username": "Your Github Username",
# "Github_token": "Your long API token",

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

github_header = {"Authorization": " token " + secrets["Github_token"]}
GH_SOURCE = "https://api.github.com/users/" + secrets["Github_username"]

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
        print("\nAttempting to GET GITHUB Stats!")  # --------------------------------
        # Print Request to Serial
        debug_request = False  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", GH_SOURCE)
        print("===============================")
        try:
            github_response = requests.get(url=GH_SOURCE, headers=github_header).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Response to Serial
        debug_response = False  # Set true to see full response
        if debug_response:
            dump_object = json.dumps(github_response)
            print("JSON Dump: ", dump_object)

        # Print Keys to Serial
        gh_debug_keys = True  # Set True to print Serial data
        if gh_debug_keys:

            github_id = github_response["id"]
            print("UserID: ", github_id)

            github_username = github_response["name"]
            print("Username: ", github_username)

            github_followers = github_response["followers"]
            print("Followers: ", github_followers)

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
