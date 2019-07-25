import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# If you have an externally connected ESP32:
# esp32_cs = DigitalInOut(board.D9)
# esp32_ready = DigitalInOut(board.D10)
# esp32_reset = DigitalInOut(board.D5)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(b'MY_SSID_NAME', b'MY_SSID_PASSWORD')
    except RuntimeError as e:
        print("could not connect to AP, retrying: ",e)
        continue
print("Connected to", str(esp.ssid, 'utf-8'), "\tRSSI:", esp.rssi)

requests.set_socket(socket, esp)

JSON_URL_GET = "http://httpbin.org/get"
JSON_URL_POST = "http://httpbin.org/post"

# Custom Header
headers = {"user-agent" : "blinka/1.0.0"}

print("Fetching JSON from %s"%JSON_URL_GET)
response = requests.get(JSON_URL_GET, headers=headers)
print('-'*40)

json_data = response.json()
print("JSON Response: ", json_data)
print('-'*40)

headers = json_data['headers']
print("Returned Custom User-Agent Header: {0}".format(headers['User-Agent']))
print('-'*40)
# Close, delete and collect the response data
response.close()

# Let's POST some data!

print("Posting data to %s..."%JSON_URL_POST)
response = requests.post(JSON_URL_POST, data="hello server!")
print('-'*40)

json_data = response.json()
print("JSON Response: ", json_data)
print('-'*40)
print("Data Returned: ", json_data['data'])
print('-'*40)
# Close, delete and collect the response data
response.close()

# Let's post some JSON data!
print("Posting JSON data to %s..."%JSON_URL_POST)
response = requests.post(JSON_URL_POST, json={"date" : "Jul 25, 2019"})
print('-'*40)

json_data = response.json()
print("JSON Response: ", json_data)
print('-'*40)
print("JSON Data Returned: ", json_data['json'])
print('-'*40)
# Close, delete and collect the response data
response.close()
