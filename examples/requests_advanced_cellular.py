import time
import board
import busio
import digitalio
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.adafruit_fona_gsm import GSM
import adafruit_fona.adafruit_fona_socket as cellular_socket
import adafruit_requests as requests

# Get GPRS details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("GPRS secrets are kept in secrets.py, please add them there!")
    raise

# Create a serial connection for the FONA connection using 4800 baud.
# These are the defaults you should use for the FONA Shield.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
uart = busio.UART(board.TX, board.RX, baudrate=4800)
rst = digitalio.DigitalInOut(board.D4)

# Initialize FONA module (this may take a few seconds)
fona = FONA(uart, rst)

# initialize gsm
gsm = GSM(fona, (secrets["apn"], secrets["apn_username"], secrets["apn_password"]))

while not gsm.is_attached:
    print("Attaching to network...")
    time.sleep(0.5)

while not gsm.is_connected:
    print("Connecting to network...")
    gsm.connect()
    time.sleep(5)

# Initialize a requests object with a socket and cellular interface
requests.set_socket(cellular_socket, fona)

JSON_GET_URL = "http://httpbin.org/get"

# Define a custom header as a dict.
headers = {"user-agent": "blinka/1.0.0"}

print("Fetching JSON data from %s..." % JSON_GET_URL)
response = requests.get(JSON_GET_URL, headers=headers)
print("-" * 60)

json_data = response.json()
headers = json_data["headers"]
print("Response's Custom User-Agent Header: {0}".format(headers["User-Agent"]))
print("-" * 60)

# Read Response's HTTP status code
print("Response HTTP Status Code: ", response.status_code)
print("-" * 60)

# Read Response, as raw bytes instead of pretty text
print("Raw Response: ", response.content)

# Close, delete and collect the response data
response.close()
