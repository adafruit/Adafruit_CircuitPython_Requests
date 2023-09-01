# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.1
# Adafruit Feather ESP32-S3 OpenSkyNetwork_Public_API_Example
import os
import time
import ssl
import json
import wifi
import socketpool
import adafruit_requests

# No login necessary for Public API. Drastically reduced daily limit vs Private
# OpenSky-Networks.org REST API: https://openskynetwork.github.io/opensky-api/rest.html
# All active flights JSON: https://opensky-network.org/api/states/all PICK ONE!
# JSON order: transponder, callsign, country
# ACTIVE transpondes only, for multiple "c822af&icao24=cb3993&icao24=c63923"
transponder = "ab1644"

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
# OpenSky-Networks will temp ban your IP for too many daily requests.
# https://openskynetwork.github.io/opensky-api/rest.html#limitations
sleep_time = 1800

# Wifi credentials pulled from settings.toml
ssid = os.getenv("AP_SSID")
appw = os.getenv("AP_PASSWORD")

# Requests URL - icao24 is their endpoint required for a transponder
# example https://opensky-network.org/api/states/all?icao24=a808c5
OPENSKY_SOURCE = "https://opensky-network.org/api/states/all?" + "icao24=" + transponder


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


def _format_datetime(datetime):
    return "{:02}/{:02}/{} {:02}:{:02}:{:02}".format(
        datetime.tm_mon,
        datetime.tm_mday,
        datetime.tm_year,
        datetime.tm_hour,
        datetime.tm_min,
        datetime.tm_sec,
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
print("Connected!\n")

while True:
    debug_request = True  # Set true to see full request
    if debug_request:
        print("Full API GET URL: ", OPENSKY_SOURCE)
    print("===============================")
    try:
        print("\nAttempting to GET OpenSky-Network Stats!")
        opensky_response = requests.get(url=OPENSKY_SOURCE)
        osn_json = opensky_response.json()
    except (ConnectionError, ValueError, NameError) as e:
        print("Host No Response Error:", e)

    # Print Full JSON to Serial
    debug_response = False  # Set true to see full response
    if debug_response:
        dump_object = json.dumps(osn_json)
        print("JSON Dump: ", dump_object)

    # Print to Serial
    osn_debug_keys = True  # Set true to print Serial data
    if osn_debug_keys:
        try:
            osn_flight = osn_json["time"]
            print("Current Unix Time: ", osn_flight)

            current_struct_time = time.localtime(osn_flight)
            current_date = "{}".format(_format_datetime(current_struct_time))
            print(f"Unix to Readable Time: {current_date}")

            osn_single_flight_data = osn_json["states"]
            if osn_single_flight_data is not None:
                print("Flight Data: ", osn_single_flight_data)
                transponder = osn_json["states"][0][0]
                print("Transponder: ", transponder)
                callsign = osn_json["states"][0][1]
                print("Callsign: ", callsign)
                country = osn_json["states"][0][2]
                print("Flight Country: ", country)
            else:
                print("This flight has no active data or you're polling too fast.")
                print(
                    "Read: https://openskynetwork.github.io/opensky-api/rest.html#limitations"
                )
                print(
                    "Public Limits: 10 second max poll rate & 400 weighted calls daily"
                )

            print("\nFinished!")
            print("Board Uptime: ", time_calc(time.monotonic()))
            print("Next Update: ", time_calc(sleep_time))
            time.sleep(sleep_time)
            print("===============================")

        except (ConnectionError, ValueError, NameError) as e:
            print("OSN Connection Error:", e)
            print("Next Retry: ", time_calc(sleep_time))
            time.sleep(sleep_time)
