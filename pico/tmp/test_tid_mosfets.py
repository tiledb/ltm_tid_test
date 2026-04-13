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

dac_steps = 8  # Adjust as needed for your application



mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 0, 0, 0, 10, 11, 12, 13, 14, 15]
mux_nr_of_channels = 20 #16
mosfet_gate_dac_ch = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 5, 5, 5, 6, 6, 6] #[0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7]
mosfet_drain_ar_adc_ch = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 0, 0, 0, 0, 0, 0]




#mosfet_gate_dac_value = [0, 0]
mosfet_gate_dac_value_readback = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
mosfet_drain_ar_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


mosfet_lot = ["dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380307", 
               "dmz380307", 
               "dmz380307", 
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307"]

mosfet_label = ["41",
                 "42",
                 "101",
                 "44",
                 "45",
                 "46",
                 "47",
                 "48",
                 "49",
                 "50",
                 "21",
                 "22",
                 "23",
                 "24",
                 "25",
                 "26",
                 "27",
                 "28",
                 "29",
                 "30"]



#round 2
# mosfet_lot = ["dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380309", 
#                "dmz380307a", 
#                "dmz380307a", 
#                "dmz380307a", 
#                "dmz380307a",
#                "dmz380307a",
#                "dmz380307a",
#                "dmz380307a",
#                "dmz380307a",
#                "dmz380307a",
#                "dmz380307a"]

# mosfet_label = ["81",
#                  "82",
#                  "83",
#                  "84",
#                  "85",
#                  "86",
#                  "87",
#                  "88",
#                  "89",
#                  "90",
#                  "61",
#                  "62",
#                  "63",
#                  "64",
#                  "65",
#                  "66",
#                  "67",
#                  "68",
#                  "69",
#                  "70"]


#round 1

# mosfet_lot = ["dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dmz380308", 
#                "dzj240155a", 
#                "dzj240155a", 
#                "dzj240155a", 
#                "dzj240155a",
#                "dzj240155a",
#                "dzj240155a",
#                "dzj240155a",
#                "dzj240155a",
#                "dzj240155a",
#                "dzj240155a"]

# mosfet_label = ["101",
#                  "102",
#                  "103",
#                  "104",
#                  "105",
#                  "106",
#                  "107",
#                  "108",
#                  "109",
#                  "110",
#                  "1",
#                  "2",
#                  "3",
#                  "4",
#                  "5",
#                  "6",
#                  "7",
#                  "8",
#                  "9",
#                  "10"]

delimiter_line = "=========="

def print_header():

    print(delimiter_line)
    first_row = "\t"
    first_row += f"requested_value\t"

    for i in range(mux_nr_of_channels):
        first_row += f"lot_{mosfet_lot[i]}_id_{mosfet_label[i]}\t"
    first_row += "\t|||\t\t"
    for i in range(mux_nr_of_channels):
        first_row += f"mosfet_gate_dac_value[{mosfet_gate_dac_ch[i]}]\tmosfet_gate_dac_value_readback[{mosfet_gate_dac_ch[i]}]\tmosfet_drain_ar_adc_value[{mosfet_drain_ar_adc_ch[i]}]_lot_{mosfet_lot[i]}_id_{mosfet_label[i]}\t|\t"
    
    print(first_row)

def mosfet_tid_test(start=0,end=4095,steps=dac_steps):

    for requested_value in range(start,end,steps): 
        row= "\t"
        for i in range(mux_nr_of_channels):
            mux.select_channel(mux_ch[i])
            #time.sleep(0.1)  # Allow mux to settle
            dac.write_and_update(mosfet_gate_dac_ch[i], requested_value)
            mosfet_gate_dac_value_readback[i] = dac.read_input(mosfet_gate_dac_ch[i])
            mosfet_drain_ar_adc_value[i] = adc.read_channel_raw(mosfet_drain_ar_adc_ch[i])
        
        row += f"{requested_value}\t"

        for i in range(mux_nr_of_channels):
            row += f"{mosfet_drain_ar_adc_value[i]}\t"
        row += "\t|||\t\t"
        for i in range(mux_nr_of_channels):
            row += f"{requested_value}\t{mosfet_gate_dac_value_readback[i]}\t{mosfet_drain_ar_adc_value[i]}\t|\t"
        print(row)
        time.sleep_ms(10)




waiting_interval = 180

print_header()
while True:
    for r in range(5):
        print(delimiter_line + "64" + delimiter_line)
        mosfet_tid_test(start=0, end=4095, steps=64)
        print(delimiter_line + "64" + delimiter_line)
        time.sleep(waiting_interval)  # Adjust delay as needed
    
    print(delimiter_line + "4" + delimiter_line)
    mosfet_tid_test(start=0, end=4095, steps=4)
    print(delimiter_line + "4" + delimiter_line)