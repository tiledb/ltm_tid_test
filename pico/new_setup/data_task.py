import time
import shared

from machine import Pin, SPI
import sys
import uselect

from cd74hc4067_driver import CD74HC4067
from mcp3208_driver import MCP3208


# -------------------------
# USB check (optional)
# -------------------------
poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)


mux = CD74HC4067(s0=26, s1=22, s2=27, s3=28)

spi_adc = SPI(1, baudrate=100000, polarity=0, phase=0,
              sck=Pin(14), mosi=Pin(15), miso=Pin(12))

adc = MCP3208(spi_adc,cs_pin=Pin(8))


mux_settle_ms = 50
adc_samples = 5
adc_settle_ms = 5


iteration = 0
max_iterations = 10


def print_header():
    shared.nprint(shared.delimiter_line)

    header = ""
    for i in range(shared.nr_of_channels):
        header += f"{shared.channel_label[i]}\t"

    shared.nprint(header)


def run():

    global iteration
    print_header()

    while not shared.stop_data_task:

        local_adc = [0] * shared.nr_of_channels
        local_avg = [0] * shared.nr_of_channels
        local_v = [0.0] * shared.nr_of_channels

        # -------------------------
        # ACQUISITION LOOP
        # -------------------------
        for i in range(shared.nr_of_channels):

            if shared.stop_data_task:
                break

            mux.select_channel(shared.mux_ch[i])
            time.sleep_ms(mux_settle_ms)

            acc = 0
            last = 0

            for _ in range(adc_samples):

                if shared.stop_data_task:
                    break

                last = adc.read_channel_raw(shared.output_adc_ch[i])
                acc += last
                time.sleep_ms(adc_settle_ms)

            avg = acc // adc_samples

            local_adc[i] = avg
            local_avg[i] = avg

            cal = shared.adc_cal
            factor = 1.0 / shared.output_adc_value_v_calibration_factor[i]
            mb_cal_factor = shared.mb_cal_factor[i]

            local_v[i] = avg * cal * factor * mb_cal_factor

        # -------------------------
        # COMMIT
        # -------------------------
        shared.data_lock.acquire()

        for i in range(shared.nr_of_channels):
            shared.output_adc_value[i] = local_adc[i]
            shared.output_adc_value_avg[i] = local_avg[i]
            shared.output_adc_value_v[i] = local_v[i]

        shared.data_lock.release()

        # -------------------------
        # PRINT
        # -------------------------
        row = ""
        if shared.raw_adc:
            # Print raw ADC values without calibration
            for i in range(shared.nr_of_channels):
                row += f"{local_adc[i]}\t"
        else:
            # Print calibrated voltage values
            for i in range(shared.nr_of_channels):
                row += f"{local_v[i]:.2f}\t"

        shared.nprint(row)

        time.sleep(0.5)