# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.2

import os
import time
import ssl
import wifi
import socketpool
import microcontroller
import adafruit_requests

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# STREAMER WARNING: private data will be viewable while debug True
debug = False  # Set True for full debug view

# Can use to confirm first instance of NVM is correct refresh token
top_nvm = microcontroller.nvm[0:64].decode()
if debug:
    print(f"Top NVM: {top_nvm}")  # NVM before settings.toml loaded

# --- Fitbit Developer Account & oAuth App Required: ---
# Required: Google Login (Fitbit owned by Google) & Fitbit Device
# Step 1: Create a personal app here: https://dev.fitbit.com
# Step 2: Use their Tutorial to get the Token and first Refresh Token
# Fitbit's Tutorial Step 4 is as far as you need to go.
# https://dev.fitbit.com/build/reference/web-api/troubleshooting-guide/oauth2-tutorial/

# Ensure these are in settings.toml
# Fitbit_ClientID = "YourAppClientID"
# Fitbit_Token = "Long 256 character string (SHA-256)"
# Fitbit_First_Refresh_Token = "64 character string"
# Fitbit_UserID = "UserID authorizing the ClientID"

Fitbit_ClientID = os.getenv("Fitbit_ClientID")
Fitbit_Token = os.getenv("Fitbit_Token")
Fitbit_First_Refresh_Token = os.getenv(
    "Fitbit_First_Refresh_Token"
)  # overides nvm first run only
Fitbit_UserID = os.getenv("Fitbit_UserID")

wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
wifi_pw = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Time between API refreshes
# 300 = 5 mins, 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900


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
        time_output = f"{sleep_int:.1f} hours"
    else:
        sleep_int = input_time / 60 / 60 / 24
        time_output = f"{sleep_int:.1f} days"
    return time_output


# Authenticates Client ID & SHA-256 Token to POST
fitbit_oauth_header = {"Content-Type": "application/x-www-form-urlencoded"}
fitbit_oauth_token = "https://api.fitbit.com/oauth2/token"

# Connect to Wi-Fi
print("\n===============================")
print("Connecting to WiFi...")
requests = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(wifi_ssid, wifi_pw)
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
print("Connected!\n")

# First run uses settings.toml token
Refresh_Token = Fitbit_First_Refresh_Token

if debug:
    print(f"Top NVM Again (just to make sure): {top_nvm}")
    print(f"Settings.toml Initial Refresh Token: {Fitbit_First_Refresh_Token}")

latest_15_avg = "Latest 15 Minute Averages"
while True:
    # Use Settings.toml refresh token on first run
    if top_nvm != Fitbit_First_Refresh_Token:
        Refresh_Token = microcontroller.nvm[0:64].decode()
        if debug:
            # NVM 64 should match Current Refresh Token
            print(f"NVM 64: {microcontroller.nvm[0:64].decode()}")
            print(f"Current Refresh_Token: {Refresh_Token}")
    else:
        if debug:
            # First run use settings.toml refresh token instead
            print(f"Initial_Refresh_Token: {Refresh_Token}")

    try:
        if debug:
            print("\n-----Token Refresh POST Attempt -------")
        fitbit_oauth_refresh_token = (
            "&grant_type=refresh_token"
            + "&client_id="
            + str(Fitbit_ClientID)
            + "&refresh_token="
            + str(Refresh_Token)
        )

        # ----------------------------- POST FOR REFRESH TOKEN -----------------------
        if debug:
            print(
                f"FULL REFRESH TOKEN POST:{fitbit_oauth_token}"
                + f"{fitbit_oauth_refresh_token}"
            )
            print(f"Current Refresh Token: {Refresh_Token}")
        # TOKEN REFRESH POST
        fitbit_oauth_refresh_POST = requests.post(
            url=fitbit_oauth_token,
            data=fitbit_oauth_refresh_token,
            headers=fitbit_oauth_header,
        )
        try:
            fitbit_refresh_oauth_json = fitbit_oauth_refresh_POST.json()

            fitbit_new_token = fitbit_refresh_oauth_json["access_token"]
            if debug:
                print("Your Private SHA-256 Token: ", fitbit_new_token)
            fitbit_access_token = fitbit_new_token  # NEW FULL TOKEN

            # If current token valid will respond
            fitbit_new_refesh_token = fitbit_refresh_oauth_json["refresh_token"]
            Refresh_Token = fitbit_new_refesh_token
            fitbit_token_expiration = fitbit_refresh_oauth_json["expires_in"]
            fitbit_scope = fitbit_refresh_oauth_json["scope"]
            fitbit_token_type = fitbit_refresh_oauth_json["token_type"]
            fitbit_user_id = fitbit_refresh_oauth_json["user_id"]
            if debug:
                print("Next Refresh Token: ", Refresh_Token)

            # Store Next Token into NVM
            try:
                nvmtoken = b"" + fitbit_new_refesh_token
                microcontroller.nvm[0:64] = nvmtoken
                if debug:
                    print(f"Next Token for NVM: {nvmtoken.decode()}")
                print("Next token written to NVM Successfully!")
            except OSError as e:
                print("OS Error:", e)
                continue

            if debug:
                # Extraneous token data for debugging
                print("Token Expires in: ", time_calc(fitbit_token_expiration))
                print("Scope: ", fitbit_scope)
                print("Token Type: ", fitbit_token_type)
                print("UserID: ", fitbit_user_id)

        except KeyError as e:
            print("Key Error:", e)
            print("Expired token, invalid permission, or (key:value) pair error.")
            time.sleep(300)
            continue

        # ----------------------------- GET DATA -------------------------------------
        # POST should respond with current & next refresh token we can GET for data
        # 64-bit Refresh tokens will "keep alive" SHA-256 token indefinitely
        # Fitbit main SHA-256 token expires in 8 hours unless refreshed!
        # ----------------------------------------------------------------------------
        detail_level = "1min"  # Supported: 1sec | 1min | 5min | 15min
        requested_date = "today"  # Date format yyyy-MM-dd or today
        fitbit_header = {
            "Authorization": "Bearer " + fitbit_access_token + "",
            "Client-Id": "" + Fitbit_ClientID + "",
        }
        # Heart Intraday Scope
        FITBIT_SOURCE = (
            "https://api.fitbit.com/1/user/"
            + Fitbit_UserID
            + "/activities/heart/date/today"
            + "/1d/"
            + detail_level
            + ".json"
        )

        print("\nAttempting to GET FITBIT Stats!")
        print("===============================")
        fitbit_get_response = requests.get(url=FITBIT_SOURCE, headers=fitbit_header)
        try:
            fitbit_json = fitbit_get_response.json()
            intraday_response = fitbit_json["activities-heart-intraday"]["dataset"]
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        if debug:
            print(f"Full API GET URL: {FITBIT_SOURCE}")
            print(f"Header: {fitbit_header}")
            # print(f"JSON Full Response: {fitbit_json}")
            # print(f"Intraday Full Response: {intraday_response}")

        try:
            # Fitbit's sync to your mobile device & server every 15 minutes in chunks.
            # Pointless to poll their API faster than 15 minute intervals.
            activities_heart_value = fitbit_json["activities-heart-intraday"]["dataset"]
            response_length = len(activities_heart_value)
            if response_length >= 15:
                activities_timestamp = fitbit_json["activities-heart"][0]["dateTime"]
                print(f"Fitbit Date: {activities_timestamp}")
                activities_latest_heart_time = fitbit_json["activities-heart-intraday"][
                    "dataset"
                ][response_length - 1]["time"]
                print(f"Fitbit Time: {activities_latest_heart_time[0:-3]}")
                print(f"Today's Logged Pulses : {response_length}")

                # Each 1min heart rate is a 60 second average
                activities_latest_heart_value0 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 1]["value"]
                activities_latest_heart_value1 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 2]["value"]
                activities_latest_heart_value2 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 3]["value"]
                activities_latest_heart_value3 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 4]["value"]
                activities_latest_heart_value4 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 5]["value"]
                activities_latest_heart_value5 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 6]["value"]
                activities_latest_heart_value6 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 7]["value"]
                activities_latest_heart_value7 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 8]["value"]
                activities_latest_heart_value8 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 9]["value"]
                activities_latest_heart_value9 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 10]["value"]
                activities_latest_heart_value10 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 11]["value"]
                activities_latest_heart_value11 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 12]["value"]
                activities_latest_heart_value12 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 13]["value"]
                activities_latest_heart_value13 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 14]["value"]
                activities_latest_heart_value14 = fitbit_json[
                    "activities-heart-intraday"
                ]["dataset"][response_length - 15]["value"]
                latest_15_avg = "Latest 15 Minute Averages"
                print(
                    f"{latest_15_avg}"
                    + f"{activities_latest_heart_value14},"
                    + f"{activities_latest_heart_value13},"
                    + f"{activities_latest_heart_value12},"
                    + f"{activities_latest_heart_value11},"
                    + f"{activities_latest_heart_value10},"
                    + f"{activities_latest_heart_value9},"
                    + f"{activities_latest_heart_value8},"
                    + f"{activities_latest_heart_value7},"
                    + f"{activities_latest_heart_value6},"
                    + f"{activities_latest_heart_value5},"
                    + f"{activities_latest_heart_value4},"
                    + f"{activities_latest_heart_value3},"
                    + f"{activities_latest_heart_value2},"
                    + f"{activities_latest_heart_value1},"
                    + f"{activities_latest_heart_value0}"
                )
            else:
                print("Waiting for latest 15 values sync...")
                print("Not enough values for today to display yet.")
                print("No display from midnight to 00:15")

        except KeyError as keyerror:
            print(f"Key Error: {keyerror}")
            print(
                "Too Many Requests, Expired token,"
                + "invalid permission,"
                + "or (key:value) pair error."
            )
            continue

        print("Board Uptime: ", time_calc(time.monotonic()))  # Board Up-Time seconds
        print("\nFinished!")
        print("Next Update in: ", time_calc(sleep_time))
        print("===============================")

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
