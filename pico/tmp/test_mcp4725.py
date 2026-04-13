from machine import Pin, I2C
from mcp4725_driver import MCP4725

# Initialize I2C (adjust pins if needed)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=100_000)
dac = MCP4725(i2c)

# Set voltage to mid-scale (2048 of 4095)
dac.write_dac(2048)

# Read back values
data = dac.read()
print("DAC Value:", data["dac"])
print("EEPROM Value:", data["eeprom"])
print("Ready:", data["ready"])