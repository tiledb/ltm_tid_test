from machine import I2C, Pin
import time
from dac7678_driver import DAC7678  # Assuming your library is saved as dac7678.py

# Initialize I2C - adjust pins for your specific board
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)  # Common ESP32 pins

try:
    # Initialize DAC (default address 0x4C)
    dac = DAC7678(i2c)
    print(f"DAC initialized at address 0x{dac.address:02X}")
    
    # Test 1: Basic output test (channel 0)
    print("\n=== Testing basic output! ===")
    for value in [0, 1024, 2048, 3072, 4095]:
        dac.write_and_update(0, value)
        readback = dac.read_input(0)
        print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V")
        time.sleep(0.5)
    
    # Test 2: Voltage setting
    print("\n=== Testing voltage output! ===")
    for voltage in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3]:
        actual_value = dac.set_voltage(0, voltage)
        actual_voltage = actual_value/4095*dac.vref
        print(f"Requested: {voltage:.2f}V | Actual: {actual_voltage:.2f}V")
        time.sleep(0.3)
    
    # Test 3: All channels individual control
    print("\n=== Testing all channels ===")
    for channel in range(8):
        value = (channel + 1) * 512 - 1  # 511, 1023, 1535, etc.
        dac.write_and_update(channel, value)
        readback = dac.read_input(channel)
        print(f"Ch{channel}: Set {value:4d} | Read {readback:4d}")
        time.sleep(0.2)
    
    # Test 4: Broadcast functions
    print("\n=== Testing broadcast functions ===")
    dac.broadcast_write(2048)
    dac.broadcast_update()
    print("All channels set to mid-scale (2048)")
    time.sleep(1)
    
    # Test 5: Waveform generation (interruptible)
    print("\n=== Testing waveform generation (10s) - press Ctrl+C to stop ===")
    try:
        dac.generate_waveforms(duration_s=10, sample_rate=100)
    except KeyboardInterrupt:
        print("Waveform test interrupted")
    
    # Final reset
    print("\nResetting all channels to zero")
    dac.reset()

except Exception as e:
    print(f"Test failed: {e}")
finally:
    print("Test complete")