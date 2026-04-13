from cd74hc4067_driver import CD74HC4067
import time

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


# Initialize DAC (default address 0x4C)
dac = DAC7678(i2c)
print(f"DAC initialized at address 0x{dac.address:02X}")

# Initialize mMUX (ch 0x00)
mux = CD74HC4067(s0=21, s1=20, s2=19, s3=18)


mux.select_channel(0)
print(f"Channel {0}")



    
def mosfet_tid_test():
    mux_ch = 0
    mux_nr_of_channels = 16
    mosfet_gate_dac_ch = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7]
    mosfet_drain_ar_adc_ch = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    #mosfet_gate_dac_value = [0, 0]
    mosfet_gate_dac_value_readback = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    mosfet_drain_ar_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    
    delimiter_line = "----------------"
    print(delimiter_line)
    first_row = ""
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_gate_dac_value[{mosfet_gate_dac_ch[i]}]\tmosfet_gate_dac_value_readback[{mosfet_gate_dac_ch[i]}]\tmosfet_drain_ar_adc_value[{mosfet_drain_ar_adc_ch[i]}]\t|\t"
    print(first_row)
    
    for requested_value in range(0,4095,64): 
        row= ""
        for i in range(mux_nr_of_channels):
            mux.select_channel(i)
            #time.sleep(0.1)  # Allow mux to settle
            dac.write_and_update(mosfet_gate_dac_ch[i], requested_value)
            mosfet_gate_dac_value_readback[i] = dac.read_input(mosfet_gate_dac_ch[i])
            mosfet_drain_ar_adc_value[i] = adc.read_channel_raw(mosfet_drain_ar_adc_ch[i])
    
            row += f"{requested_value}\t{mosfet_gate_dac_value_readback[i]}\t\t{mosfet_drain_ar_adc_value[i]}\t|\t"
        print(row)    



mosfet_tid_test()