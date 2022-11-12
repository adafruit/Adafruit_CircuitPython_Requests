# SPDX-FileCopyrightText: 2022 DJDevon3 for Adafruit Industries
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.0
"""DJDevon3 Adafruit Feather ESP32-S2 Discord_API_Example"""
import gc
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# Active Logged in User Account Required, no tokens required
# WEB SCRAPE authorization key required. Visit URL below.
# Learn how: https://github.com/lorenz234/Discord-Data-Scraping

# Ensure this is in secrets.py or .env
# "Discord_Authorization": "Discord Authorization from browser console"

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

discord_header = {"Authorization": "" + secrets["Discord_Authorization"]}
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
        wifi.radio.connect(secrets["ssid"], secrets["password"])
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
    gc.collect()
print("Connected!\n")

while True:
    try:
        print(
            "\nAttempting to GET DISCORD PREVIEW!"
        )  # --------------------------------
        # Print Request to Serial
        debug_request = False  # Set true to see full request
        if debug_request:
            print("Full API GET URL: ", ADA_SOURCE)
        print("===============================")
        try:
            ada_res = requests.get(url=ADA_SOURCE, headers=discord_header).json()
        except ConnectionError as e:
            print("Connection Error:", e)
            print("Retrying in 10 seconds")

        # Print Full JSON to Serial
        discord_debug_response = False  # Change to true to see full response
        if discord_debug_response:
            ada_discord_dump_object = json.dumps(ada_res)
            print("JSON Dump: ", ada_discord_dump_object)

        # Print keys to Serial
        discord_debug_keys = True  # Set to True to print Serial data
        if discord_debug_keys:

            ada_discord_all_members = ada_res["approximate_member_count"]
            print("Members: ", ada_discord_all_members)

            ada_discord_all_members_online = ada_res["approximate_presence_count"]
            print("Online: ", ada_discord_all_members_online)

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
