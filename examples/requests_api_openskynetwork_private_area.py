# SPDX-FileCopyrightText: 2023 DJDevon3
# SPDX-License-Identifier: MIT
# Coded for Circuit Python 8.1
# DJDevon3 ESP32-S3 OpenSkyNetwork_Private_Area_API_Example

import os
import time
import ssl
import json
import wifi
import socketpool
import circuitpython_base64 as base64
import adafruit_requests

# OpenSky-Network.org Website Login required for this API
# REST API: https://openskynetwork.github.io/opensky-api/rest.html

# Retrieves all traffic within a geographic area (Orlando example)
latmin = "27.22"  # east bounding box
latmax = "28.8"  # west bounding box
lonmin = "-81.46"  # north bounding box
lonmax = "-80.40"  # south bounding box

# Initialize WiFi Pool (There can be only 1 pool & top of script)
pool = socketpool.SocketPool(wifi.radio)

# Time between API refreshes
# 900 = 15 mins, 1800 = 30 mins, 3600 = 1 hour
# OpenSky-Networks IP bans for too many requests, check rate limit.
# https://openskynetwork.github.io/opensky-api/rest.html#limitations
sleep_time = 1800

# this example uses settings.toml for credentials
# No token required, only website login
ssid = os.getenv("AP_SSID")
appw = os.getenv("AP_PASSWORD")
osnu = os.getenv("OSN_Username")
osnp = os.getenv("OSN_Password")

osn_cred = str(osnu) + ":" + str(osnp)
bytes_to_encode = b" " + str(osn_cred) + " "
base64_string = base64.encodebytes(bytes_to_encode)
base64cred = repr(base64_string)[2:-1]

Debug_Auth = False  # STREAMER WARNING this will show your credentials!
if Debug_Auth:
    osn_cred = str(osnu) + ":" + str(osnp)
    bytes_to_encode = b" " + str(osn_cred) + " "
    print(repr(bytes_to_encode))
    base64_string = base64.encodebytes(bytes_to_encode)
    print(repr(base64_string)[2:-1])
    base64cred = repr(base64_string)[2:-1]
    print("Decoded Bytes:", str(base64cred))

# OSN requires your username:password to be base64 encoded
# so technically it's not transmitted in the clear but w/e
osn_header = {"Authorization": "Basic " + str(base64cred)}

# Example request of all traffic over Florida, geographic areas cost less per call.
# https://opensky-network.org/api/states/all?lamin=25.21&lomin=-84.36&lamax=30.0&lomax=-78.40
OPENSKY_SOURCE = (
    "https://opensky-network.org/api/states/all?"
    + "lamin="
    + latmin
    + "&lomin="
    + lonmin
    + "&lamax="
    + latmax
    + "&lomax="
    + lonmax
)


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
request = adafruit_requests.Session(pool, ssl.create_default_context())
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(ssid, appw)
    except ConnectionError as e:
        print("Connection Error:", e)
        print("Retrying in 10 seconds")
    time.sleep(10)
print("Connected!\n")

while True:
    # STREAMER WARNING this will show your credentials!
    debug_request = False  # Set True to see full request
    if debug_request:
        print("Full API HEADER: ", str(osn_header))
        print("Full API GET URL: ", OPENSKY_SOURCE)
        print("===============================")

    print("\nAttempting to GET OpenSky-Network Data!")
    opensky_response = request.get(url=OPENSKY_SOURCE, headers=osn_header).json()

    # Print Full JSON to Serial (doesn't show credentials)
    debug_response = False  # Set True to see full response
    if debug_response:
        dump_object = json.dumps(opensky_response)
        print("JSON Dump: ", dump_object)

    # Key:Value Serial Debug (doesn't show credentials)
    osn_debug_keys = True  # Set True to print Serial data
    if osn_debug_keys:
        try:
            osn_flight = opensky_response["time"]
            print("Current Unix Time: ", osn_flight)

            current_struct_time = time.localtime(osn_flight)
            current_date = "{}".format(_format_datetime(current_struct_time))
            print(f"Unix to Readable Time: {current_date}")

            # Current flight data for single callsign (right now)
            osn_all_flights = opensky_response["states"]

            if osn_all_flights is not None:
                # print("Flight Data: ", osn_all_flights)
                for flights in osn_all_flights:
                    osn_t = f"Trans:{flights[0]} "
                    osn_c = f"Sign:{flights[1]} "
                    osn_o = f"Origin:{flights[2]} "
                    osn_tm = f"Time:{flights[3]} "
                    osn_l = f"Last:{flights[4]} "
                    osn_lo = f"Lon:{flights[5]} "
                    osn_la = f"Lat:{flights[6]} "
                    osn_ba = f"BaroAlt:{flights[7]} "
                    osn_g = f"Ground:{flights[8]} "
                    osn_v = f"Vel:{flights[9]} "
                    osn_h = f"Head:{flights[10]} "
                    osn_vr = f"VertRate:{flights[11]} "
                    osn_s = f"Sens:{flights[12]} "
                    osn_ga = f"GeoAlt:{flights[13]} "
                    osn_sq = f"Squawk:{flights[14]} "
                    osn_pr = f"Task:{flights[15]} "
                    osn_ps = f"PosSys:{flights[16]} "
                    osn_ca = f"Cat:{flights[16]} "
                    # This is just because pylint complains about long lines
                    string1 = f"{osn_t}{osn_c}{osn_o}{osn_tm}{osn_l}{osn_lo}"
                    string2 = f"{osn_la}{osn_ba}{osn_g}{osn_v}{osn_h}{osn_vr}"
                    string3 = f"{osn_s}{osn_ga}{osn_sq}{osn_pr}{osn_ps}{osn_ca}"
                    print(f"{string1}{string2}{string3}")
            else:
                print("Flight has no active data or you're polling too fast.")

            print("\nFinished!")
            print("Board Uptime: ", time_calc(time.monotonic()))
            print("Next Update: ", time_calc(sleep_time))
            time.sleep(sleep_time)
            print("===============================")

        except (ConnectionError, ValueError, NameError) as e:
            print("OSN Connection Error:", e)
            print("Next Retry: ", time_calc(sleep_time))
            time.sleep(sleep_time)
