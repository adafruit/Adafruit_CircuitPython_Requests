# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.2.x
# Twitch_API_Example

import os
import time
import ssl
import wifi
import socketpool
import adafruit_requests

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Twitch Developer Account & oauth App Required:
# Visit https://dev.twitch.tv/console to create an app

# Ensure these are in secrets.py or settings.toml
# "Twitch_ClientID": "Your Developer APP ID Here",
# "Twitch_Client_Secret": "APP ID secret here",
# "Twitch_UserID": "Your Twitch UserID here",

# Use settings.toml for credentials
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
appw = os.getenv("CIRCUITPY_WIFI_PASSWORD")
twitch_client_id = os.getenv("Twitch_ClientID")
twitch_client_secret = os.getenv("Twitch_Client_Secret")
# For finding your Twitch User ID
# https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/
twitch_user_id = os.getenv("Twitch_UserID")  # User ID you want endpoints from

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900


# Converts seconds to minutes/hours/days
def time_calc(input_time):
    if input_time < 60:
        return f"{input_time:.0f} seconds"
    if input_time < 3600:
        return f"{input_time / 60:.0f} minutes"
    if input_time < 86400:
        return f"{input_time / 60 / 60:.0f} hours"
    return f"{input_time / 60 / 60 / 24:.1f} days"


# First we use Client ID & Client Secret to create a token with POST
# No user interaction is required for this type of scope (implicit grant flow)
twitch_0auth_header = {"Content-Type": "application/x-www-form-urlencoded"}
TWITCH_0AUTH_TOKEN = "https://id.twitch.tv/oauth2/token"

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.connected:
    try:
        wifi.radio.connect(ssid, appw)
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
print("Connected!\n")

while True:
    try:
        # ----------------------------- POST FOR BEARER TOKEN -----------------------
        print(
            "Attempting Bearer Token Request!"
        )  # ---------------------------------------
        # Print Request to Serial
        debug_bearer_request = (
            False  # STREAMER WARNING: your client secret will be viewable
        )
        if debug_bearer_request:
            print("Full API GET URL: ", TWITCH_0AUTH_TOKEN)
        print("===============================")
        twitch_0auth_data = (
            "&client_id="
            + twitch_client_id
            + "&client_secret="
            + twitch_client_secret
            + "&grant_type=client_credentials"
        )

        # POST REQUEST
        twitch_0auth_response = requests.post(
            url=TWITCH_0AUTH_TOKEN, data=twitch_0auth_data, headers=twitch_0auth_header
        )
        try:
            twitch_0auth_json = twitch_0auth_response.json()
            twitch_access_token = twitch_0auth_json["access_token"]
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Response to Serial
        debug_bearer_response = (
            False  # STREAMER WARNING: your client secret will be viewable
        )
        if debug_bearer_response:
            print("JSON Dump: ", twitch_0auth_json)
            print("Header: ", twitch_0auth_header)
            print("Access Token: ", twitch_access_token)
            twitch_token_type = twitch_0auth_json["token_type"]
            print("Token Type: ", twitch_token_type)

        print("Board Uptime: ", time_calc(time.monotonic()))
        twitch_token_expiration = twitch_0auth_json["expires_in"]
        print("Token Expires in: ", time_calc(twitch_token_expiration))

        # ----------------------------- GET DATA -------------------------------------
        # Bearer token is refreshed every time script runs :)
        # Twitch sets token expiration to about 64 days
        # Helix is the name of the current Twitch API
        # Now that we have POST bearer token we can do a GET for data
        # ----------------------------------------------------------------------------
        twitch_header = {
            "Authorization": "Bearer " + twitch_access_token + "",
            "Client-Id": "" + twitch_client_id + "",
        }
        TWITCH_FOLLOWERS_SOURCE = (
            "https://api.twitch.tv/helix/channels"
            + "/followers?"
            + "broadcaster_id="
            + twitch_user_id
        )
        print(
            "\nAttempting to GET TWITCH Stats!"
        )  # ------------------------------------------------
        print("===============================")
        twitch_followers_response = requests.get(
            url=TWITCH_FOLLOWERS_SOURCE, headers=twitch_header
        )
        try:
            twitch_followers_json = twitch_followers_response.json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Response to Serial
        debug_bearer_response = (
            False  # STREAMER WARNING: your bearer token will be viewable
        )
        if debug_bearer_response:
            print("Full API GET URL: ", TWITCH_FOLLOWERS_SOURCE)
            print("Header: ", twitch_header)
            print("JSON Full Response: ", twitch_followers_json)

        twitch_followers = twitch_followers_json["total"]
        print("Followers: ", twitch_followers)
        print("Finished!")
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
