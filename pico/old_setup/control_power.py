from machine import Pin, SPI, I2C
import time
import sys
import uselect

poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)


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
SKU21284_relay.all_on()


# Initialize the MUX (CD4051BE)
mux = CD4051BE(a=13, b=14, c=15)



# Turn on power supply
psu.power_on()
ltm.all_on()
mux_channel=0
while True:

    # ---- check for keypress (non-blocking) ----
    if poller.poll(0):          # 0 ms timeout = non-blocking
        key = sys.stdin.read(1)

        if key == 't':
            print("ALL ON")
            psu.power_on()
            SKU21284_relay.all_on()
            ltm.all_on()

        elif key == 'f':
            print("ALL OFF")
            ltm.all_off()
            SKU21284_relay.all_off()
            psu.power_off()

    # ---- normal loop work ----
    print("power good:", psu.is_power_good())
    time.sleep(2)
