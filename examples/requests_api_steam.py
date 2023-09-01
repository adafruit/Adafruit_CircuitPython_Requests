# SPDX-FileCopyrightText: 2022 DJDevon3 (Neradoc & Deshipu helped) for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 api_steam Example"""
import os
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Steam API Docs: https://steamcommunity.com/dev
# Steam API Key: https://steamcommunity.com/dev/apikey
# Steam Usernumber: Visit https://steamcommunity.com
# click on your profile icon, your usernumber will be in the browser url.

# Ensure these are setup in settings.toml
# Requires Steam Developer API key
ssid = os.getenv("AP_SSID")
appw = os.getenv("AP_PASSWORD")
steam_usernumber = os.getenv("steam_id")
steam_apikey = os.getenv("steam_api_key")

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900

# Deconstruct URL (pylint hates long lines)
# http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/
# ?key=XXXXXXXXXXXXXXXXXXXXX&include_played_free_games=1&steamid=XXXXXXXXXXXXXXXX&format=json
Steam_OwnedGames_URL = (
    "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?"
    + "key="
    + steam_apikey
    + "&include_played_free_games=1"
    + "&steamid="
    + steam_usernumber
    + "&format=json"
)

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
        print("\nAttempting to GET STEAM Stats!")  # --------------------------------
        # Print Request to Serial
        debug_request = False  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", Steam_OwnedGames_URL)
        print("===============================")
        try:
            steam_response = requests.get(url=Steam_OwnedGames_URL).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Response to Serial
        debug_response = False  # Set true to see full response
        if debug_response:
            dump_object = json.dumps(steam_response)
            print("JSON Dump: ", dump_object)

        # Print Keys to Serial
        steam_debug_keys = True  # Set True to print Serial data
        if steam_debug_keys:
            game_count = steam_response["response"]["game_count"]
            print("Total Games: ", game_count)
            total_minutes = 0

            for game in steam_response["response"]["games"]:
                total_minutes += game["playtime_forever"]
            total_hours = total_minutes / 60
            total_days = total_minutes / 60 / 24
            print(f"Total Hours: {total_hours}")
            print(f"Total Days: {total_days}")

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
