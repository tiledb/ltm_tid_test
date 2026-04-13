import _thread
import time
import sys

import data_task
from atxpsu_driver import atxpsu
from ltm_run_driver import ltm_run


# -----------------------------
# GLOBAL CONTROL
# -----------------------------
stop_flag = False
thread_alive = False


# -----------------------------
# HARDWARE
# -----------------------------
psu = atxpsu(ps_on_pin=0, invert_polarity=False, delay_ms=200)
ltm = ltm_run([1, 9, 10, 11, 13], active_low=False)


# SAFE BOOT STATE (IMPORTANT)
psu.power_off()
time.sleep(0.2)
psu.power_on()


# -----------------------------
# THREAD FUNCTION (YOUR WHILE TRUE)
# -----------------------------
def data_thread():
    global thread_alive, stop_flag

    thread_alive = True

    try:
        while True:

            # -------------------------
            # EXIT CONDITION (KILL SWITCH)
            # -------------------------
            if stop_flag:
                break

            # -------------------------
            # YOUR ORIGINAL FUNCTION
            # -------------------------
            data_task.run()

    except KeyboardInterrupt:
        print("Thread: KeyboardInterrupt")

    except Exception as e:
        print("Thread CRASH:", e)

    finally:
        thread_alive = False
        print("Thread exited safely")


# -----------------------------
# START THREAD
# -----------------------------
def start_thread():
    global stop_flag
    stop_flag = False
    _thread.start_new_thread(data_thread, ())


# -----------------------------
# STOP THREAD (COOPERATIVE KILL)
# -----------------------------
def stop_thread():
    global stop_flag
    stop_flag = True


# -----------------------------
# MAIN
# -----------------------------
def main():
    global stop_flag

    start_thread()

    try:
        while True:
            ltm.all_on()
            time.sleep(5)
            ltm.all_off()
            time.sleep(5)

    # -------------------------
    # CTRL+C HANDLING
    # -------------------------
    except KeyboardInterrupt:
        print("CTRL+C -> stopping system")

    # -------------------------
    # ANY CRASH IN MAIN
    # -------------------------
    except Exception as e:
        print("MAIN CRASH:", e)

    finally:
        print("Stopping thread...")

        stop_thread()
        time.sleep(0.5)

        # HARD SAFE SHUTDOWN
        try:
            ltm.all_off()
        except:
            pass

        psu.power_off()
        print("PSU OFF")


# -----------------------------
# START
# -----------------------------
main()