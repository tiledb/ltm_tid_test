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

def mosfet_test():
    
    mosfet_gate_dac_ch = 1
    mosfet_drain_dac_ch = 0
    mosfet_drain_br_adc_ch = 0
    mosfet_drain_ar_adc_ch = 1
    mosfet_gate_adc_ch = 2

    mosfet_gate_dac_value = 0
    mosfet_gate_dac_value_readback = 0
    mosfet_drain_dac_value = 4095  # Full scale for testing
    mosfet_gate_adc_value = 0
    mosfet_drain_br_adc_value = 0
    mosfet_drain_ar_adc_value = 0
    
    dac.write_and_update(mosfet_drain_dac_ch, mosfet_drain_dac_value)
    
    first_row = f"mosfet_gate_dac_value[{mosfet_gate_dac_ch}] \t mosfet_gate_dac_value_readback[{mosfet_gate_dac_ch}] \t mosfet_drain_dac_value[{mosfet_drain_dac_ch}] \t mosfet_gate_adc_value[{mosfet_gate_adc_ch}] \t mosfet_drain_br_adc_value[{mosfet_drain_br_adc_ch}] \t mosfet_drain_ar_adc_value[{mosfet_drain_ar_adc_ch}] \t"
    print(first_row)
    
    for mosfet_gate_dac_value in range(0,4095): 
        #print(f"mosfet_gate_dac_ch: {mosfet_gate_dac_ch}")
        dac.write_and_update(mosfet_gate_dac_ch, mosfet_gate_dac_value)
        mosfet_gate_dac_value_readback = dac.read_input(mosfet_gate_dac_ch)
        mosfet_drain_br_adc_value = adc.read_channel_raw(mosfet_drain_br_adc_ch)
        mosfet_drain_ar_adc_value = adc.read_channel_raw(mosfet_drain_ar_adc_ch)
        mosfet_gate_adc_value = adc.read_channel_raw(mosfet_gate_adc_ch)
   
        row = f"{mosfet_gate_dac_value}\t{mosfet_gate_dac_value_readback}\t{mosfet_drain_dac_value}\t{mosfet_gate_adc_value}\t{mosfet_drain_br_adc_value}\t{mosfet_drain_ar_adc_value}\t"
        print(row)    


def swipe_all_channels():
    # Test 1: Basic output test (channel 0)
    print("\n=== Testing basic output! ===")

    the_dac_readback_values = [0,0,0,0,0,0,0,0]
    the_adc_raw_values = [0,0,0,0,0,0,0,0]
    the_voltage_values = [0.,0.,0.,0.,0.,0.,0.,0.]

    first_row = ""
    for ch in range(8):  # Assuming we have 8 channels
        first_row += f"Value requested \t the_dac_readback_values[{ch}] \t value[{ch}]/4095*dac.vref \t the_adc_raw_values[{ch}] \t the_voltage_values[{ch}]\t"
    print(first_row)
    
    for value in range(0,4095): #[0, 1024, 2048, 3072, 4095]:
        for ch in range(8):  # Assuming we have 8 channels
            dac.write_and_update(ch, value)
            readback = dac.read_input(ch)
            raw = adc.read_channel_raw(ch)
            voltage = adc.read_channel_voltage(ch)
            
            the_dac_readback_values[ch] = readback
            the_adc_raw_values[ch] = raw
            the_voltage_values[ch] = voltage
        
        row=""
        for ch in range(8):
            row += f"{value:4d}\t{the_dac_readback_values[ch]:4d}\t{value/4095*dac.vref:.2f}\t{the_adc_raw_values[ch]:4d}\t{the_voltage_values[ch]:.2f}\t"
        
        print(row)
    
        #print(f"{value:4d}\t{readback:4d}\t{value/4095*dac.vref:.2f}\t{raw:4d}\t{voltage:.2f}")
        #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V, Raw: {raw:4d}, Voltage: {voltage:.2f}V")

# print(f"Set \t | Readback: \t | Voltage: \t | Raw: \t | Voltage:")
# for value in range(0,4095): #[0, 1024, 2048, 3072, 4095]:
#     dac.write_and_update(1, value)
#     readback = dac.read_input(1)
#     raw = adc.read_channel_raw(1)
#     voltage = adc.read_channel_voltage(1)
#     print(f"{value:4d}\t{readback:4d}\t{value/4095*dac.vref:.2f}\t{raw:4d}\t{voltage:.2f}")
#     #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V, Raw: {raw:4d}, Voltage: {voltage:.2f}V")
    
#     #print(f"Set: {value:4d} | Readback: {readback:4d} | Voltage: {value/4095*dac.vref:.2f}V")
#     #adc_read_all_channels()
#     #time.sleep(0.5)
        