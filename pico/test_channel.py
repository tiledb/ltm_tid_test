from machine import Pin, SPI, I2C
import time

# Import your drivers (make sure they are on the Pico)
from atxpsu_driver import atxpsu
from sku21284_driver import SKU21284
from cd4051be_driver import CD4051BE
from mcp3208_driver import MCP3208
from ltm_run_driver import ltm_run
# Basic usage without power good monitoring
psu = atxpsu(ps_on_pin=0, invert_polarity=False, power_good_pin=1, delay_ms=200)

SKU21284_relay = SKU21284(relay1_pin=6, relay2_pin=7, active_low=False)
ltm = ltm_run([8, 9, 10, 11, 12], active_low=False)

# SKU21284_relay.test_relay()
SKU21284_relay.all_on()

# Initialize the MUX (CD4051BE)
mux = CD4051BE(a=13, b=14, c=15)

# Initialize the ADC (MCP3208)
spi_adc = SPI(0, baudrate=100000, polarity=0, phase=0,
             sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_adc = Pin(5, Pin.OUT)
run_pin = Pin(9, Pin.OUT)

adc = MCP3208(spi_adc, cs_adc)

nr_of_channels = 36
mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 
          0, 1, 2, 3, 4, 5, 6, 7, 
          0, 1, 2, 3, 4, 5, 6, 7, 
          0, 1, 2, 3, 4, 5, 6, 7, 
          0, 0, 0, 0]
ltm_output_adc_ch = [0, 0, 0, 0, 0, 0, 0, 0, 
                     1, 1, 1, 1, 1, 1, 1, 1, 
                     2, 2, 2, 2, 2, 2, 2, 2, 
                     3, 3, 3, 3, 3, 3, 3, 3, 
                     4, 5, 6, 7]
ltm_output_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0]

ltm_output_adc_value_v = [0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 
                        0, 0, 0, 0]

adc_resolution = 4096  # 12-bit ADC
adc_reference_voltage = 3.3  # Reference voltage for ADC in volts
adc_cal = adc_reference_voltage / adc_resolution  # Volts per ADC count
mux_volt_div = 1/(1/2)
atx_volt_div = 1/(1.2/(3.9+1.2))
ltm_output_adc_value_v_calibration_factor = [mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div*atx_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, 
                        mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, 
                        mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, 
                        mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, mux_volt_div, 
                        1, 1, 1, 1]




channel_label = ["mon_c2",             "mon_c1",             "mon_d2",             "atx_v",             "pg_e",             "mon_d1",             "pg_d",             "pg_c",
            "run_c",             "run_b",             "run_a",             "run_d",             "pg_b",             "pi_3v3",             "pg_a",             "run_e",
            "mon_e2",             "e2_out",             "mon_e1",             "d1_out",             "e1_out",             "mon_b2",             "d2_out",             "c1_out",
            "mon_b1",             "b1_out",             "c2_out",             "b2_out",             "a1_out",             "mon_a2",             "mon_a1",             "a2_out",
             "gnd",             "gnd",             "gnd",             "gnd"]



ltm_lot = ["4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4"]

ltm_label = ["1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
             "10",             "11",             "12",             "13"]




# Turn on power supply
psu.power_on()
ltm.all_on()


mux_channel=0
adc_channel=1
adc_value=0
phase=0

channel=12

while(1):
    
    print("power good: ", psu.is_power_good())
    
    # Select MUX channel
    # mux.select_channel(mux_channel)
    # if mux_channel < 7:
    #     mux_channel = (mux_channel + 1)
    # else:
    #     mux_channel = 0
    # print("Selecting MUX channel: ", mux_channel)
    
    # Select MUX channel
    # phase=not phase
    # run_pin.value(phase)  # Enable run
    
    
    mux.select_channel(mux_ch[channel])
    # mux.select_channel(mux_channel)
    time.sleep(2)
    
    ltm_output_adc_value=adc.read_channel_raw(ltm_output_adc_ch[channel])
    # adc_value = adc.read_channel_raw(adc_channel)
    ltm_output_adc_value_v= ltm_output_adc_value * adc_cal * ltm_output_adc_value_v_calibration_factor[channel]
    print(f"Channel: {channel} - MUX Channel: {mux_ch[channel]}, ADC Channel: {ltm_output_adc_ch[channel]}, ADC Value: {ltm_output_adc_value}, Voltage: {ltm_output_adc_value_v:.3f} V")
    # print(f"MUX Channel: {mux_channel}, ADC Channel: {adc_channel}, ADC Value: {adc_value}")
    
    
    # ltm.test()
    
    
    
    