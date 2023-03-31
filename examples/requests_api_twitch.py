# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Twitch_API_Example"""
import gc
import time
import ssl
import wifi
import socketpool
import adafruit_requests

# Twitch Developer Account & 0Auth App Required:
# Visit https://dev.twitch.tv/console to create an app
# Ensure Twitch_ClientID & Twitch_Client_Secret are in secrets.py or .env

# "Twitch_ClientID": "Your Developer APP ID Here",
# "Twitch_Client_Secret": "APP ID secret here",

# For finding your Twitch User ID
# https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/
Twitch_UserID = "0000000"  # Set User ID you want endpoints from

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


# First we use Client ID & Client Secret to create a token with POST
# No user interaction is required for this type of scope (implicit grant flow)
twitch_0auth_header = {"Content-Type": "application/x-www-form-urlencoded"}
TWITCH_0AUTH_TOKEN = "https://id.twitch.tv/oauth2/token"

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
        # ----------------------------- POST FOR BEARER TOKEN -----------------------
        print(
            "\nAttempting to GENERATE Twitch Bearer Token!"
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
            + secrets["Twitch_ClientID"]
            + "&client_secret="
            + secrets["Twitch_Client_Secret"]
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

        twitch_token_expiration = twitch_0auth_json["expires_in"]
        print("Token Expires in: ", time_calc(twitch_token_expiration))
        twitch_token_type = twitch_0auth_json["token_type"]
        print("Token Type: ", twitch_token_type)
        print("Monotonic: ", time.monotonic())

        # ----------------------------- GET DATA -------------------------------------
        # Bearer token is refreshed every time script runs :)
        # Twitch sets token expiration to about 64 days
        # Helix is the name of the current Twitch API
        # Now that we have POST bearer token we can do a GET for data
        # ----------------------------------------------------------------------------
        twitch_header = {
            "Authorization": "Bearer " + twitch_access_token + "",
            "Client-Id": "" + secrets["Twitch_ClientID"] + "",
        }
        TWITCH_FOLLOWERS_SOURCE = (
            "https://api.twitch.tv/helix/users"
            + "/follows?"
            + "to_id="
            + Twitch_UserID
            + "&first=1"
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

        twitch_username = twitch_followers_json["data"][0]["to_name"]
        print("Username: ", twitch_username)
        twitch_followers = twitch_followers_json["total"]
        print("Followers: ", twitch_followers)
        print("Monotonic: ", time.monotonic())  # Board Up-Time seconds

        print("\nFinished!")
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")
        gc.collect()

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
