# SPDX-FileCopyrightText: 2022 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Mastodon_API_Example"""
import gc
import time
import ssl
import wifi
import socketpool
import adafruit_requests

# Mastodon V1 API - Public access (no dev creds or app required)
# Visit https://docs.joinmastodon.org/client/public/ for API docs
# For finding your Mastodon User ID
# Login to your mastodon server in a browser, visit your profile, UserID is in the URL.
# Example: https://mastodon.YOURSERVER/web/accounts/YOURUSERIDISHERE

Mastodon_Server = "mastodon.social"  # Set server instance
Mastodon_UserID = "000000000000000000"  # Set User ID you want endpoints from
# Test in browser first, this will pull up a JSON webpage
# https://mastodon.YOURSERVER/api/v1/accounts/YOURUSERIDHERE/statuses?limit=1

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
MAST_SOURCE = (
    "https://"
    + Mastodon_Server
    + "/api/v1/accounts/"
    + Mastodon_UserID
    + "/statuses?limit=1"
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
        print("\nAttempting to GET MASTODON Stats!")  # -----------------------------
        # Print Request to Serial
        debug_mastodon_full_response = (
            False  # STREAMER WARNING: your client secret will be viewable
        )
        print("===============================")
        mastodon_response = requests.get(url=MAST_SOURCE)
        try:
            mastodon_json = mastodon_response.json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")
        mastodon_json = mastodon_json[0]
        if debug_mastodon_full_response:
            print("Full API GET URL: ", MAST_SOURCE)
            print(mastodon_json)
            mastodon_userid = mastodon_json["account"]["id"]
            print("User ID: ", mastodon_userid)

        mastodon_username = mastodon_json["account"]["display_name"]
        print("Name: ", mastodon_username)
        mastodon_join_date = mastodon_json["account"]["created_at"]
        print("Member Since: ", mastodon_join_date)
        mastodon_toot_count = mastodon_json["account"]["statuses_count"]
        print("Toots: ", mastodon_toot_count)
        mastodon_follower_count = mastodon_json["account"]["followers_count"]
        print("Followers: ", mastodon_follower_count)
        print("Monotonic: ", time.monotonic())

        print("\nFinished!")
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")
        gc.collect()

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
