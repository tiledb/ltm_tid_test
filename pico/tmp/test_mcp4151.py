from machine import SPI, Pin
import time
from mcp4151_driver import MCP4151  # Adjust if your file name is different

# Initialize SPI (adjust pins as per your board)
spi = SPI(1, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(14), mosi=Pin(15), miso=Pin(12))  # MISO is unused by MCP4151

cs_pin = 13  # Chip Select pin (adjust as needed)
#cs_pin = 18  # Chip Select pin (adjust as needed)

# Create MCP4151 instance
pot = MCP4151(spi, cs_pin)
# pot.debug = True  # Optional: enable debug output

value=100
converted_value = int(255 - value/5000*255)
pot.set_resistance(converted_value)  # Set to mid-scale for 5k potentiometer
time.sleep(100)


# Test 1: Set resistance to min, mid, and max
print("Test 1: Setting resistance to 0, 128, and 255")
pot.set_resistance(0)
time.sleep(1)

pot.set_resistance(128)
time.sleep(1)

pot.set_resistance(255)
time.sleep(1)

# Test 2: Increment and decrement
print("Test 2: Increment and Decrement")
pot.set_resistance(100)
time.sleep(0.5)

pot.increment(10)  # Should go to 110
time.sleep(0.5)

pot.decrement(20)  # Should go to 90
time.sleep(0.5)

# Test 3: Percent-based setting
print("Test 3: Set resistance by percent")
for p in [0, 25, 50, 75, 100]:
    pot.set_resistance_percent(p)
    time.sleep(0.5)

# Test 4: Boundary checks
print("Test 4: Boundary conditions")
pot.set_resistance(-10)  # Should clamp to 0
time.sleep(0.5)

pot.set_resistance(300)  # Should clamp to 255
time.sleep(0.5)

pot.set_resistance_percent(-50)  # Should clamp to 0%
time.sleep(0.5)

pot.set_resistance_percent(150)  # Should clamp to 100%
time.sleep(0.5)

# Print current state
print("Final wiper position:", pot.get_resistance())
