# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import adafruit_connection_manager
import board
import busio
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
from digitalio import DigitalInOut
import ssl
import adafruit_requests

if hasattr(board, 'W5500_CS'):
    # Wiznet W5500-EVB-Pico
    cs = DigitalInOut(board.W5500_CS)
    reset = DigitalInOut(board.W5500_RST)
else:
    # Adafruit Ethernet Featherwing
    cs = DigitalInOut(board.D10)
    reset = None

spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize ethernet interface with DHCP
radio = WIZNET5K(spi_bus, cs, reset=reset)

# Initialize a requests session
pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl_context)

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "http://httpbin.org/get"
JSON_GET_URL = "https://httpbin.org/get"
JSON_POST_URL = "https://httpbin.org/post"

if __name__ == '__main__':
    print("Fetching text from %s" % TEXT_URL)
    with requests.get(TEXT_URL) as response:
        print("-" * 40)

        print("Text Response: ", response.text)
        print("-" * 40)

    print("Fetching JSON data from %s" % JSON_GET_URL)
    with requests.get(JSON_GET_URL) as response:
        print(response)
        print("-" * 40)

        print("JSON Response: ", response.json())
        print("-" * 40)

    data = "31F"
    print("POSTing data to {0}: {1}".format(JSON_POST_URL, data))
    with requests.post(JSON_POST_URL, data=data) as response:
        print("-" * 40)

        json_resp = response.json()
        # Parse out the 'data' key from json_resp dict.
        print("Data received from server:", json_resp["data"])
        print("-" * 40)

    json_data = {"Date": "July 25, 2019"}
    print("POSTing data to {0}: {1}".format(JSON_POST_URL, json_data))
    with requests.post(JSON_POST_URL, json=json_data) as response:
        print("-" * 40)

        json_resp = response.json()
        # Parse out the 'json' key from json_resp dict.
        print("JSON Data received from server:", json_resp["json"])
        print("-" * 40)
