# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 YouTube_API_Example"""
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Ensure these are uncommented and in secrets.py or .env
# "YT_username": "Your YouTube Username",
# "YT_token" : "Your long API developer token",

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

# https://youtube.googleapis.com/youtube/v3/channels?part=statistics&forUsername=[YOUR_USERNAME]&key=[YOUR_API_KEY]
YT_SOURCE = (
    "https://youtube.googleapis.com/youtube/v3/channels?"
    + "part=statistics"
    + "&forUsername="
    + secrets["YT_username"]
    + "&key="
    + secrets["YT_token"]
)

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
        print("Attempting to GET YouTube Stats!")  # ----------------------------------
        debug_request = False  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", YT_SOURCE)
        print("===============================")
        try:
            response = requests.get(YT_SOURCE).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Full JSON to Serial
        debug_response = False  # Set true to see full response
        if debug_response:
            dump_object = json.dumps(response)
            print("JSON Dump: ", dump_object)

        # Print to Serial
        yt_debug_keys = True  # Set to True to print Serial data
        if yt_debug_keys:
            print("Matching Results: ", response["pageInfo"]["totalResults"])

            YT_request_kind = response["items"][0]["kind"]
            print("Request Kind: ", YT_request_kind)

            YT_response_kind = response["kind"]
            print("Response Kind: ", YT_response_kind)

            YT_channel_id = response["items"][0]["id"]
            print("Channel ID: ", YT_channel_id)

            YT_videoCount = response["items"][0]["statistics"]["videoCount"]
            print("Videos: ", YT_videoCount)

            YT_viewCount = response["items"][0]["statistics"]["viewCount"]
            print("Views: ", YT_viewCount)

            YT_subsCount = response["items"][0]["statistics"]["subscriberCount"]
            print("Subscribers: ", YT_subsCount)
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
