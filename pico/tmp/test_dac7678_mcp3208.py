from machine import SPI, I2C, Pin
import time
from dac7678_driver import DAC7678
from mcp3208_driver import MCP3208

# SPI configuration — adjust pins as per your microcontroller and wiring
spi_adc = SPI(0, baudrate=400000, polarity=0, phase=0,
          sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_pin_adc = Pin(5, Pin.OUT)
# Create MCP3208 instance with debug mode on
adc = MCP3208(spi=spi_adc, cs_pin=cs_pin_adc, vref=3.3)

# Initialize I2C - adjust pins for your specific board
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)  # Common ESP32 pins


def adc_read_all_channels():
    """Read all channels of the MCP3208 ADC."""
    all_channels = adc.read_all_channels()
    for ch, raw, voltage in all_channels:
        print(f"Channel {ch}: Raw = {raw:4d}, Voltage = {voltage:.4f} V")


# Initialize DAC (default address 0x4C)
dac = DAC7678(i2c)
print(f"DAC initialized at address 0x{dac.address:02X}")

    # Test 1: Basic output test (channel 0)
print("\n=== Testing basic output! ===")
print(f"Set \t | Readback: \t | Voltage: \t | Raw: \t | Voltage:")
for value in range(0,4095): #[0, 1024, 2048, 3072, 4095]:
    dac.write_and_update(0, value)
    readback = dac.read_input(0)
    raw = adc.read_channel_raw(0)
    voltage = adc.read_channel_voltage(0)
    print(f"{value:4d}\t{readback:4d}\t{value/4095*dac.vref:.2f}\t{raw:4d}\t{voltage:.2f}")
    #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V, Raw: {raw:4d}, Voltage: {voltage:.2f}V")

print(f"Set \t | Readback: \t | Voltage: \t | Raw: \t | Voltage:")
for value in range(0,4095): #[0, 1024, 2048, 3072, 4095]:
    dac.write_and_update(1, value)
    readback = dac.read_input(1)
    raw = adc.read_channel_raw(1)
    voltage = adc.read_channel_voltage(1)
    print(f"{value:4d}\t{readback:4d}\t{value/4095*dac.vref:.2f}\t{raw:4d}\t{voltage:.2f}")
    #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V, Raw: {raw:4d}, Voltage: {voltage:.2f}V")
    
    #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V")
    #adc_read_all_channels()
    #time.sleep(0.5)
        