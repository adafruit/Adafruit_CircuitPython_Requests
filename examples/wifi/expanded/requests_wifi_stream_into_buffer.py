# SPDX-FileCopyrightText: 2026 Vladimir Smitka
# SPDX-License-Identifier: MIT
"""Read a large response into a reused buffer, so it needs no memory beyond the buffer"""

import gc
import os

import adafruit_connection_manager
import wifi

import adafruit_requests

URL = "https://httpbin.org/bytes/40000"

wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

buffer = bytearray(1024)
for attempt in range(5):
    gc.collect()
    total = 0
    with requests.get(URL, stream=True) as response:
        while True:
            read = response.raw.readinto(buffer)
            if read == 0:
                break
            # Use buffer[:read] here, for example write it to a file or a Bitmap.
            total += read
    gc.collect()
    print(f"Download {attempt}: {total} bytes, {gc.mem_free()} bytes free")
