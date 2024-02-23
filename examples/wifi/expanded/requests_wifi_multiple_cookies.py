# SPDX-FileCopyrightText: 2022 Alec Delaney
# SPDX-License-Identifier: MIT

"""
This example was written for the MagTag; changes may be needed
for connecting to the internet depending on your device.
"""

import os
import ssl

import socketpool
import wifi

import adafruit_requests

COOKIE_TEST_URL = "https://www.adafruit.com"

# Get WiFi details, ensure these are setup in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

# Connect to the Wi-Fi network
print("Connecting to %s" % ssid)
wifi.radio.connect(ssid, password)

# Set up the requests library
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# GET from the URL
print("Fetching multiple cookies from", COOKIE_TEST_URL)
response = requests.get(COOKIE_TEST_URL)

# Spilt up the cookies by ", "
elements = response.headers["set-cookie"].split(", ")

# NOTE: Some cookies use ", " when describing dates.  This code will iterate through
# the previously split up 'set-cookie' header value and piece back together cookies
# that were accidentally split up for this reason
days_of_week = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
elements_iter = iter(elements)
cookie_list = []
for element in elements_iter:
    captured_day = [day for day in days_of_week if element.endswith(day)]
    if captured_day:
        cookie_list.append(element + ", " + next(elements_iter))
    else:
        cookie_list.append(element)

# Pring the information about the cookies
print("Number of cookies:", len(cookie_list))
print("")
print("Cookies received:")
print("-" * 40)
for cookie in cookie_list:
    print(cookie)
    print("-" * 40)
