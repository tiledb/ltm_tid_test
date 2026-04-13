from machine import SPI, Pin
from mcp4151_driver import MCP4151
from mcp3208_driver import MCP3208


import time

# Initialize SPI bus (to be shared by all MCP4151 devices)
spi = SPI(0,
          baudrate=1_000_000,  # MCP4151 supports up to 10MHz
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(2),
          mosi=Pin(3),
          miso=Pin(4))

# Initialize two potentiometers with different CS pins
pot1 = MCP4151(spi, cs_pin=22)  # CS on GP22
pot2 = MCP4151(spi, cs_pin=18)  # CS on GP18

# Initialize MCP3208 with CS on GP5
adc = MCP3208(spi, cs_pin=5, vref=3.3)

def main():
    # Example 1: Simple sweep
    print("Running sweep demo...")
    for i in range(256):
        pot1.set_resistance(i)
        pot2.set_resistance(255 - i)
        time.sleep_ms(10)
    
    # Example 2: Using percentage control
    print("Setting to 50%...")
    pot1.set_resistance_percent(50)
    pot2.set_resistance_percent(50)
    time.sleep(1)
    
    # Example 3: Using increment/decrement
    print("Incrementing/decrementing...")
    for _ in range(10):
        pot1.increment(5)
        pot2.decrement(5)
        time.sleep_ms(100)
    
    # Example 4: Reading current value
    print("Current values:")
    print(f"Pot 1: {pot1.get_resistance()} ({(pot1.get_resistance()/255)*100:.1f}%)")
    print(f"Pot 2: {pot2.get_resistance()} ({(pot2.get_resistance()/255)*100:.1f}%)")


    print("=== MCP3208 Diagnostic Test ===")
    
    # Test SPI connection
    # if adc.validate_spi_connection():
    #     print("SPI Communication: OK")
    # else:
    #     print("SPI Communication: FAILED")
    #     return
    
    # Continuous reading of all channels
    print("\nReading all channels (Ctrl+C to stop):")
    print("CH | Raw  | Voltage")
    print("-------------------")
    
    try:
        while True:
            for ch, raw, voltage in adc.read_all_channels():
                print(f"{ch:2d} | {raw:4d} | {voltage:.2f}V", end=" | ")
            print()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped by user")

if __name__ == "__main__":
    main()
