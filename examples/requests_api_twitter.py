# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Twitter_API_Example"""
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Twitter developer account bearer token required.
# Ensure these are uncommented and in secrets.py or .env
# "TW_userid": "Your Twitter user id",  # numerical id not username
# "TW_bearer_token": "Your long API Bearer token",

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

# Used with any Twitter 0auth request.
twitter_header = {"Authorization": "Bearer " + secrets["TW_bearer_token"]}
TW_SOURCE = (
    "https://api.twitter.com/2/users/"
    + secrets["TW_userid"]
    + "?user.fields=public_metrics,created_at,pinned_tweet_id"
    + "&expansions=pinned_tweet_id"
    + "&tweet.fields=created_at,public_metrics,source,context_annotations,entities"
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
        print("\nAttempting to GET Twitter Stats!")  # --------------------------------
        debug_request = False  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", TW_SOURCE)
        print("===============================")
        try:
            twitter_response = requests.get(url=TW_SOURCE, headers=twitter_header)
            tw_json = twitter_response.json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Full JSON to Serial
        debug_response = False  # Set true to see full response
        if debug_response:
            dump_object = json.dumps(tw_json)
            print("JSON Dump: ", dump_object)

        # Print to Serial
        tw_debug_keys = True  # Set true to print Serial data
        if tw_debug_keys:
            tw_userid = tw_json["data"]["id"]
            print("User ID: ", tw_userid)

            tw_username = tw_json["data"]["name"]
            print("Name: ", tw_username)

            tw_join_date = tw_json["data"]["created_at"]
            print("Member Since: ", tw_join_date)

            tw_tweets = tw_json["data"]["public_metrics"]["tweet_count"]
            print("Tweets: ", tw_tweets)

            tw_followers = tw_json["data"]["public_metrics"]["followers_count"]
            print("Followers: ", tw_followers)

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
