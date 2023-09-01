# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.2
# DJDevon3 Adafruit Feather ESP32-S3 Discord API Example
import os
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Active Logged in User Account Required, no tokens required
# WEB SCRAPE authorization key required. Visit URL below.
# Learn how: https://github.com/lorenz234/Discord-Data-Scraping

# Ensure this is in settings.toml
# "Discord_Authorization": "Request Header Auth here"

# Uses settings.toml for credentials
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
appw = os.getenv("CIRCUITPY_WIFI_PASSWORD")
Discord_Auth = os.getenv("Discord_Authorization")

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# API Polling Rate
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
sleep_time = 900


# Converts seconds to human readable minutes/hours/days
def time_calc(input_time):  # input_time in seconds
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


discord_header = {"Authorization": "" + Discord_Auth}
ADA_SOURCE = (
    "https://discord.com/api/v10/guilds/"
    + "327254708534116352"  # Adafruit Discord ID
    + "/preview"
)

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
print("Connected!✅")

while True:
    try:
        print("\nAttempting to GET Discord Data!")  # --------------------------------
        # STREAMER WARNING this will show your credentials!
        debug_request = False  # Set True to see full request
        if debug_request:
            print("Full API GET URL: ", ADA_SOURCE)
        print("===============================")
        try:
            ada_res = requests.get(url=ADA_SOURCE, headers=discord_header).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Full JSON to Serial
        discord_debug_response = False  # Set True to see full response
        if discord_debug_response:
            ada_discord_dump_object = json.dumps(ada_res)
            print("JSON Dump: ", ada_discord_dump_object)

        # Print keys to Serial
        discord_debug_keys = True  # Set True to print Serial data
        if discord_debug_keys:
            ada_discord_all_members = ada_res["approximate_member_count"]
            print("Members: ", ada_discord_all_members)

            ada_discord_all_members_online = ada_res["approximate_presence_count"]
            print("Online: ", ada_discord_all_members_online)

        print("Finished ✅")
        print("Board Uptime: ", time_calc(time.monotonic()))
        print("Next Update: ", time_calc(sleep_time))
        print("===============================")

    except (ConnectionError, ValueError, NameError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(60)
        continue
    time.sleep(sleep_time)
