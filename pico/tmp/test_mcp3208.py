from machine import Pin, SPI
import time

# Import the MCP3208 class if it's in another module
from mcp3208_driver import MCP3208

# SPI configuration — adjust pins as per your microcontroller and wiring
spi = SPI(0, baudrate=400000, polarity=0, phase=0,
          sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_pin = Pin(5, Pin.OUT)

# Create MCP3208 instance with debug mode on
adc = MCP3208(spi=spi, cs_pin=cs_pin, vref=3.3)

# Validate SPI connection
print("\n--- SPI Connection Test ---")
if adc.validate_spi_connection():
    print("SPI connection appears functional.")
else:
    print("SPI connection failed or unreliable.")

# Read and display all channels
print("\n--- Reading All Channels ---")
all_channels = adc.read_all_channels()
for ch, raw, voltage in all_channels:
    print(f"Channel {ch}: Raw = {raw:4d}, Voltage = {voltage:.4f} V")

# Read a specific channel
print("\n--- Single Channel Read (Channel 0) ---")
raw = adc.read_channel_raw(0)
voltage = adc.read_channel_voltage(0)
print(f"Channel 0 Raw: {raw}")
print(f"Channel 0 Voltage: {voltage:.4f} V")

# Optional: loop to read repeatedly
print("\n--- Repeated Reads (Every 1s) ---")
try:
    while True:
        all_channels = adc.read_all_channels()
        for ch, raw, voltage in all_channels:
            print(f"Channel {ch}: Raw = {raw:4d}, Voltage = {voltage:.4f} V")
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped by user.")
