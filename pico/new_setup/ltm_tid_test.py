import _thread
import time
import sys
from machine import WDT

import shared
import data_task
from atxpsu_driver import atxpsu
from ltm_run_driver import ltm_run


# -------------------------
# COMMAND LINE ARGUMENTS
# -------------------------
def parse_args():
    """Parse command line arguments manually for MicroPython compatibility"""
    global WATCHDOG_ENABLED, PSU_ON, shared
    
    # Default values
    WATCHDOG_ENABLED = False
    PSU_ON = True
    
    # Parse arguments - use script_args if available, otherwise empty list
    args = script_args if 'script_args' in globals() else []
    
    for arg in args:
        if arg == '--watchdog-enable':
            WATCHDOG_ENABLED = True
        elif arg == '--watchdog-disable' or arg == '--no-watchdog':
            WATCHDOG_ENABLED = False
        elif arg == '--psu-on':
            PSU_ON = True
        elif arg == '--psu-off':
            PSU_ON = False
        elif arg == '--raw-adc':
            shared.raw_adc = True
        elif arg == '--calibrated-adc':
            shared.raw_adc = False
        elif arg.startswith('--mb'):
            # Handle MB argument: --mb1, --mb2, etc.
            try:
                mb_num = int(arg[4:])  # Extract number after --mb
                shared.set_mb_calibration(mb_num)
            except (ValueError, IndexError):
                print("Warning: Invalid MB format, using default MB0")
        elif arg == '--help' or arg == '-h':
            print_help()
            return  # Exit function instead of sys.exit
    
    print(f"Settings: Watchdog={'ON' if WATCHDOG_ENABLED else 'OFF'}, PSU={'ON' if PSU_ON else 'OFF'}, Raw ADC={'ON' if shared.raw_adc else 'OFF'}, MB={shared.mb_number}")

def print_help():
    """Print help message"""
    print("LTM TID Test - Usage:")
    print("  python ltm_tid_test.py [options]")
    print("")
    print("Options:")
    print("  --watchdog-enable    Enable watchdog timer")
    print("  --watchdog-disable   Disable watchdog timer (default)")
    print("  --psu-on            Enable power supply on startup (default)")
    print("  --psu-off           Disable power supply on startup")
    print("  --raw-adc           Output raw ADC values (default)")
    print("  --calibrated-adc    Output calibrated voltage values")
    print("  --mb1, --mb2, etc.  Select motherboard calibration (default: --mb1)")
    print("  --help, -h          Show this help message")

# Parse arguments
parse_args()


# -------------------------
# WATCHDOG
# -------------------------
wdt = WDT(timeout=5000) if WATCHDOG_ENABLED else None


def feed_wdt():
    if WATCHDOG_ENABLED:
        wdt.feed()


# -------------------------
# HARDWARE
# -------------------------
psu = atxpsu(ps_on_pin=0, invert_polarity=False, delay_ms=200)
ltm = ltm_run([1, 9, 10, 11, 13], active_low=True)


# SAFE BOOT
# psu.power_off()
time.sleep(0.2)
if PSU_ON:
    psu.power_on()
else:
    psu.power_off()


thread_alive = False


def data_thread():
    global thread_alive

    thread_alive = True

    try:
        data_task.run()

    except Exception as e:
        print("THREAD CRASH:", e)

    finally:
        thread_alive = False
        print("THREAD EXITED")


def start_thread():
    shared.stop_data_task = False
    _thread.start_new_thread(data_thread, ())


def stop_thread():
    shared.stop_data_task = True


# -------------------------
# MAIN
# -------------------------
start_thread()

# Initialize power control
current_time = time.time()
shared.initialize_power_control(current_time)

try:
    while True:
        current_time = time.time()
        
        # Update power states
        atx_on = shared.update_atx_power_state(current_time)
        ltm_on = shared.update_ltm_power_state(current_time)
        
        # Control hardware based on power states
        if atx_on:
            psu.power_on()
            if ltm_on:
                ltm.all_on()
            else:
                ltm.all_off()
        else:
            psu.power_off()
            ltm.all_off()
        
        feed_wdt()
        time.sleep(0.1)  # Faster update for better timing control

except KeyboardInterrupt:
    print("CTRL+C -> stopping")

finally:
    print("Shutting down...")

    psu.power_off()
    print("PSU OFF")

    stop_thread()
    time.sleep(0.5)

