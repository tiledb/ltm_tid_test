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
mux = CD74HC4067(s0=20, s1=21, s2=18, s3=19)


mux.select_channel(0)
print(f"Channel {0}")


    
def mosfet_tid_test(iterations=1, steps=1):
    print("Starting MOSFET TID test...")
    if steps < 1 or steps > 4095:
        raise ValueError("Steps must be between 1 and 4095.")
    else:
        print(f"Running test with steps: {steps}")
    if iterations > 0:
        for i in range(iterations):
            print(f"Running iteration {i + 1} of {iterations}")
            run_mosfet_tid_test(steps)
    elif iterations == 0:
        print("No iterations specified, running single test.")
        while True:
            run_mosfet_tid_test(steps)

    
def run_mosfet_tid_test(steps=1):
   
    mux_nr_of_channels = 16
    mosfet_gate_dac_ch = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7]
    mosfet_drain_ar_adc_ch = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    #mosfet_gate_dac_value = [0, 0]
    mosfet_gate_dac_value_readback = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    mosfet_drain_ar_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    
    delimiter_line = "----------------"
    print(delimiter_line)
    first_row = "requested_value\t"
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_drain_ar_adc_value[{mosfet_drain_ar_adc_ch[i]}]_mux_channel[{i}]\t"
    first_row += "|\t"
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_gate_dac_value_readback[{mosfet_gate_dac_ch[i]}]\t"
    first_row += "|\t"
    print(first_row)
    
    for requested_value in range(0,4095,steps): 
        row= f"{requested_value}\t"
        for i in range(mux_nr_of_channels):
            mux.select_channel(i)
            #time.sleep(0.1)  # Allow mux to settle
            dac.write_and_update(mosfet_gate_dac_ch[i], requested_value)
            mosfet_gate_dac_value_readback[i] = dac.read_input(mosfet_gate_dac_ch[i])
            mosfet_drain_ar_adc_value[i] = adc.read_channel_raw(mosfet_drain_ar_adc_ch[i])
    
            row += f"{mosfet_drain_ar_adc_value[i]}\t"    
        row += "|\t"
        for i in range(mux_nr_of_channels):
            row += f"{mosfet_gate_dac_value_readback[i]}\t"
        row += "|\t"
        print(row)    
    print(delimiter_line)

def one_mosfet_test(ch=0, steps=1):
    the_steps = 1
    the_ch= 0
    print("Starting MOSFET TID test for one channel...")
    if steps < 1 or steps > 4095:
        print(f"Error on the number of steps... testing with steps: {the_steps}")
    else:
        the_steps = steps
        print(f"Running test with steps: {the_steps}")
        
        
    if ch < 0 or ch > 15:
        print(f"Channel must be between 0 and 15. Defaulting to channel 0.")
    else:
        print(f"Running test for channel {ch}")
        the_ch = ch
        
    
    mux_nr_of_channels = 1
    mosfet_gate_dac_ch = [0]
    mosfet_drain_ar_adc_ch = [0]
    
    #mosfet_gate_dac_value = [0, 0]
    mosfet_gate_dac_value_readback = [0]
    mosfet_drain_ar_adc_value = [0]

    
    delimiter_line = "----------------"
    print(delimiter_line)
    first_row = "requested_value\t"
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_drain_ar_adc_value[{mosfet_drain_ar_adc_ch[i]}]_mux_channel[{the_ch}]\t"
    first_row += "|\t"
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_gate_dac_value_readback[{mosfet_gate_dac_ch[i]}]\t"
    first_row += "|\t"
    print(first_row)
    
    for requested_value in range(0,4095,the_steps): 
        row= f"{requested_value}\t"
        for i in range(mux_nr_of_channels):
            mux.select_channel(the_ch)
            #time.sleep(0.1)  # Allow mux to settle
            dac.write_and_update(mosfet_gate_dac_ch[i], requested_value)
            mosfet_gate_dac_value_readback[i] = dac.read_input(mosfet_gate_dac_ch[i])
            mosfet_drain_ar_adc_value[i] = adc.read_channel_raw(mosfet_drain_ar_adc_ch[i])
    
            row += f"{mosfet_drain_ar_adc_value[i]}\t"    
        row += "|\t"
        for i in range(mux_nr_of_channels):
            row += f"{mosfet_gate_dac_value_readback[i]}\t"
        row += "|\t"
        print(row)    
    print(delimiter_line)
