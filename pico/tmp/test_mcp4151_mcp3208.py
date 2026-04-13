from machine import SPI, Pin
import time
from mcp4151_driver import MCP4151  # Adjust if your file name is different
from mcp3208_driver import MCP3208


# Initialize SPI (adjust pins as per your board)
spi_pot = SPI(1, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))  # MISO is unused by MCP4151

cs_pin_pot = [22,18]  # Chip Select pin (adjust as needed)

# Create MCP4151 instance
pots = [MCP4151(spi_pot, cs_pin_pot[0]), MCP4151(spi_pot, cs_pin_pot[1])]




# SPI configuration — adjust pins as per your microcontroller and wiring
spi_adc = SPI(0, baudrate=400000, polarity=0, phase=0,
          sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_pin_adc = Pin(5, Pin.OUT)
# Create MCP3208 instance with debug mode on
adc = MCP3208(spi=spi_adc, cs_pin=cs_pin_adc, vref=3.3)

def adc_read_all_channels():
    """Read all channels of the MCP3208 ADC."""
    all_channels = adc.read_all_channels()
    for ch, raw, voltage in all_channels:
        print(f"Channel {ch}: Raw = {raw:4d}, Voltage = {voltage:.4f} V")
        
print("Test 3: Set resistance by percent")
for p in range(0,100): # [0, 25, 50, 75, 100]:
    print(f"Setting pot 1 to {p}% and pot 2 to {100-p}%")
    pots[0].set_resistance_percent(p)
    pots[1].set_resistance_percent(100-p)
    adc_read_all_channels()
    time.sleep(0.5)
