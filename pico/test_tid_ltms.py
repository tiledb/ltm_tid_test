from machine import Pin, SPI, I2C
import sys
import uselect
import time

poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)

# Import your drivers (make sure they are on the Pico)
from cd4051be_driver import CD4051BE
from mcp3208_driver import MCP3208
from atxpsu_driver import atxpsu
from ltm_run_driver import ltm_run
from sku21284_driver import SKU21284


# Basic usage without power good monitoring
psu = atxpsu(ps_on_pin=0, invert_polarity=False, power_good_pin=1, delay_ms=200)

SKU21284_relay = SKU21284(relay1_pin=6, relay2_pin=7, active_low=False)
ltm = ltm_run([8, 9, 10, 11, 12], active_low=False)

# SKU21284_relay.test_relay()
SKU21284_relay.on(1)

# Turn on power supply
psu.power_on()
print("power good: ", psu.is_power_good())
ltm.all_on()

time.sleep(2)



# Initialize the MUX (CD4051BE)
mux = CD4051BE(a=13, b=14, c=15)

# Initialize the ADC (MCP3208)
spi_adc = SPI(0, baudrate=100000, polarity=0, phase=0,
             sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_adc = Pin(5, Pin.OUT)
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
voltage_calibration_value = 12.2/10.03


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

# DAC sweep range (0-4095 for 12-bit DAC)

delimiter_line = "=========="
first_row = "atx_power_good\t"
mux_row = "atx_power_good\t"
adc_row = "atx_power_good\t"
channel_label_row = "atx_pg\t"
info_row = "atx_power_good\t"


def print_header():
    print(delimiter_line)
    global first_row, mux_row, adc_row, channel_label_row, info_row
    # first_row = "atx_power_good\t"
    # mux_row = "atx_power_good\t"
    # adc_row = "atx_power_good\t"
    # channel_label_row = "atx_power_good\t"
    # first_row += f"requested_value\t"

    for i in range(nr_of_channels):
        first_row += f"lot_{ltm_lot[i]}_id_{ltm_label[i]}\t"
        mux_row += f"mux_ch_{mux_ch[i]}\t"
        adc_row += f"adc_ch_{ltm_output_adc_ch[i]}\t"
        channel_label_row += f"{channel_label[i]}\t"
        info_row += f"{channel_label[i]}_adc[{ltm_output_adc_ch[i]}]_mux[{mux_ch[i]}]\t"
        
    first_row += "\t|||\t\t"
  
    print(first_row)
    print(info_row)



phase=0
iteration = 0
max_iterations = 10

mux_settle_ms = 50  # time to wait after changing MUX channel
adc_samples = 10   # choose how many samples to average
adc_settle_ms = 5   # small delay between samples (adjust if needed)

def ltm_tid_test():
    global iteration, info_row, channel_label_row
    global phase

    if iteration < max_iterations:
        iteration += 1
    else:
        iteration = 0
        print("--"+channel_label_row+"--")
        phase=not phase
        
        
        
    # if phase == 0:
    #     ltm.all_on()
    # else:
    #     # ltm.all_on()
    #     iteration+=(max_iterations-1)
    #     ltm.all_off()
        
    for i in range(nr_of_channels):
        mux.select_channel(mux_ch[i])
        time.sleep_ms(mux_settle_ms)  # Allow settling time
        acc = 0
        for _ in range(adc_samples):
            acc += adc.read_channel_raw(ltm_output_adc_ch[i])
            time.sleep_ms(adc_settle_ms)

        ltm_output_adc_value[i] = acc // adc_samples  # integer average

        # ltm_output_adc_value[i] = adc.read_channel_raw(ltm_output_adc_ch[i])
        ltm_output_adc_value_v[i] = ltm_output_adc_value[i] * adc_cal * ltm_output_adc_value_v_calibration_factor[i] # * voltage_calibration_value
    atxpsu_pgood = psu.is_power_good()
    row_adc = f"{atxpsu_pgood}\t"
    row_v = f"{atxpsu_pgood}\t"
    for i in range(nr_of_channels):
        row_adc += f"{ltm_output_adc_value[i]}\t"
        row_v += f"{ltm_output_adc_value_v[i]:.3f}V\t"
    print(f"{row_adc}")
    print(f"--{row_v}--")




waiting_interval = 180  # seconds

def main():
    print_header()
    print("--"+channel_label_row+"--")
    while True:

        # print(delimiter_line + delimiter_line)
        ltm_tid_test()
        if poller.poll(0):          # non-blocking
            cmd = sys.stdin.read(1)

            if cmd == 't':
                print("CMD: ALL ON")
                psu.power_on()
                SKU21284_relay.all_on()
                # ltm.all_on()

            elif cmd == 'f':
                print("CMD: ALL OFF")
                # ltm.all_off()
                SKU21284_relay.all_off()
                psu.power_off()        
        # print(delimiter_line + delimiter_line)



if __name__ == "__main__":
    main()
    
    