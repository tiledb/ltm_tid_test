import _thread

# -------------------------
# PRINT CONTROL
# -------------------------
cprint_enabled = True
nprint_enabled = True
delimiter_line = "=========="

def cprint(msg):
    if cprint_enabled:
        try:
            print("--" + str(msg) + "--")
        except OSError:
            pass

def nprint(msg):
    if nprint_enabled:
        try:
            print(msg)
        except OSError:
            pass


# -------------------------
# THREAD CONTROL FLAG
# -------------------------
stop_data_task = False

# -------------------------
# ADC OUTPUT CONTROL
# -------------------------
raw_adc = False  # When True, print raw ADC values without calibration


# -------------------------
# HARDWARE CONFIG
# -------------------------
nr_of_channels = 27

mux_ch = [
    0,1,2,3,4,5,6,7,8,9,10,11,12,
    0,1,2,3,4,5,6,7,8,9,10,11,12,
    13
]

output_adc_ch = [
    2,2,2,2,2,2,2,2,2,2,2,2,2,
    0,0,0,0,0,0,0,0,0,0,0,0,0,
    4
]

# -------------------------
# DATA STORAGE
# -------------------------
output_adc_value = [0]*nr_of_channels
output_adc_value_avg = [0]*nr_of_channels
output_adc_value_v = [0.0]*nr_of_channels


# -------------------------
# CALIBRATION (NUMERIC ONLY)
# -------------------------
adc_resolution = 4096
adc_reference_voltage = 3.3
adc_cal = adc_reference_voltage / adc_resolution

pg_x_cal = 47000. / (47000. + 47000.)
v_x_cal = 1000. / (1000. + 1000.)
v_12v_cal = 3300. / (3300. + 8200.)
c_x_cal = 0.002* (12000./100.)

# IMPORTANT: numeric only (NO STRINGS)
output_adc_value_v_calibration_factor = [
    v_x_cal, pg_x_cal, c_x_cal, pg_x_cal, v_x_cal, pg_x_cal, c_x_cal, c_x_cal, c_x_cal, v_x_cal, v_x_cal, c_x_cal, v_x_cal,
    c_x_cal, v_x_cal, v_12v_cal, v_x_cal, c_x_cal, v_x_cal, pg_x_cal, pg_x_cal, v_x_cal, c_x_cal, c_x_cal, v_x_cal, c_x_cal,
    pg_x_cal
]


channel_label = [
    "v_e1","pg_e","c_e1","pg_d","v_e2","pg_c","c_e2","c_d1", "c_d2","v_d1","v_d2","c_c1","v_c1",
    "c_c2","v_c2","v_12v","v_b1","c_b1","v_b2","pg_b", "pg_a","v_a1","c_b2","c_a1","v_a2","c_a2",
    "pg_12v"
]


# -------------------------
# THREAD LOCK
# -------------------------
data_lock = _thread.allocate_lock()