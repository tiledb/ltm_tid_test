from machine import Pin, SPI, I2C
import time

# Import your drivers (make sure they are on the Pico)
from atxpsu_driver import atxpsu
from sku21284_driver import SKU21284
from cd4051be_driver import CD4051BE
from ltm_run_driver import ltm_run

# Basic usage without power good monitoring
psu = atxpsu(ps_on_pin=0, invert_polarity=False, power_good_pin=1, delay_ms=200)

SKU21284_relay = SKU21284(relay1_pin=6, relay2_pin=7, active_low=False)

ltm = ltm_run([8, 9, 10, 11, 12], active_low=True)


# SKU21284_relay.test_relay()
SKU21284_relay.all_off()



# Initialize the MUX (CD4051BE)
mux = CD4051BE(a=13, b=14, c=15)



# Turn on power supply
psu.power_off()
ltm.all_off()
mux_channel=0
while(1):
    
    print("power good: ", psu.is_power_good())
    
    # Select MUX channel
    # mux.select_channel(mux_channel)
    # if mux_channel < 7:
    #     mux_channel = (mux_channel + 1)
    # else:
    #     mux_channel = 0
    # print("Selecting MUX channel: ", mux_channel)
    ltm
    time.sleep(2)