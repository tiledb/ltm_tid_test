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
# MB CALIBRATION CONTROL
# -------------------------
mb_number = 0  # Default MB number (can be changed via arguments)

# MB calibration factors for different motherboards
mb_calibration_factors = {
    0: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0],
    1: [1.0, 1.0, 0.3571428571, 1.0, 1.0, 1.0, 0.2265005663, 0.2242152466, 0.1984126984, 1.0, 1.0, 0.2751031637, 1.0,
        0.2178649237, 1.0, 1.0, 1.0, 0.2127659574, 1.0, 1.0, 1.0, 1.0, 0.3189792663, 0.1926782274, 1.0, 0.2259887006,
        1.0],
    2: [1.0, 1.0, 0.4282655246, 1.0, 1.0, 1.0, 0.283286119, 0.2617801047, 0.245398773, 1.0, 1.0, 0.3120124805, 1.0,
        0.2614379085, 1.0, 1.0, 1.0, 0.2577319588, 1.0, 1.0, 1.0, 1.0, 0.3773584906, 0.2398081535, 1.0, 0.2789400279,
        1.0],
    # Add more MB calibration arrays here as needed
    # 2: cal_mb2,
    # 3: cal_mb3,
}

mb_power_config = {
    0: {"atx_on": 0, "atx_off": 0, "ltm_on": 0, "ltm_off": 0},
    1: {"atx_on": 0, "atx_off": 0, "ltm_on": 0, "ltm_off": 0},
    2: {"atx_on": 15.0, "atx_off": 5.0, "ltm_on": 3.0, "ltm_off": 1.0},
    # 2: {"atx_on": 120.0, "atx_off": 5.0, "ltm_on": 30.0, "ltm_off": 5.0},
}

mb_poff_config = {
    0: {"atx": 1.0, "ltm": 1.0},
    1: [1.0, 1.0, 0.3571428571, 1.0, 1.0, 1.0, 0.2265005663, 0.2242152466, 0.1984126984, 1.0, 1.0, 0.2751031637, 1.0,
        0.2178649237, 1.0, 1.0, 1.0, 0.2127659574, 1.0, 1.0, 1.0, 1.0, 0.3189792663, 0.1926782274, 1.0, 0.2259887006,
        1.0],
    2: [1.0, 1.0, 0.4282655246, 1.0, 1.0, 1.0, 0.283286119, 0.2617801047, 0.245398773, 1.0, 1.0, 0.3120124805, 1.0,
        0.2614379085, 1.0, 1.0, 1.0, 0.2577319588, 1.0, 1.0, 1.0, 1.0, 0.3773584906, 0.2398081535, 1.0, 0.2789400279,
        1.0],
    # Add more MB calibration arrays here as needed
    # 2: cal_mb2,
    # 3: cal_mb3,
}

# Current MB calibration factor array (will be set based on mb_number)
mb_cal_factor = mb_calibration_factors[mb_number]

# Current MB power config (will be set based on mb_number)
mb_current_power_config = mb_power_config[mb_number]

def set_mb_calibration(mb_num):
    """Update the MB calibration factor based on MB number"""
    global mb_number, mb_cal_factor
    if mb_num in mb_calibration_factors:
        mb_number = mb_num
        mb_cal_factor = mb_calibration_factors[mb_num]
        update_mb_power_config()
        print(f"MB calibration set to MB{mb_num}")
    else:
        print(f"Warning: MB{mb_num} calibration not found, using default MB0")
        mb_number = 0
        mb_cal_factor = mb_calibration_factors[0]
        update_mb_power_config()

def get_mb_power_config(mb_num=None):
    """Get the power configuration for the specified MB number"""
    if mb_num is None:
        mb_num = mb_number
    
    if mb_num in mb_power_config:
        return mb_power_config[mb_num]
    else:
        print(f"Warning: MB{mb_num} power config not found, using default MB0")
        return mb_power_config[0]

def update_mb_power_config():
    """Update the current power config based on mb_number"""
    global mb_current_power_config
    mb_current_power_config = mb_power_config.get(mb_number, mb_power_config[0])

# Power control state variables
atx_power_state = True  # True = ON, False = OFF
ltm_power_state = True  # True = ON, False = OFF
atx_timer_start = 0
ltm_timer_start = 0

def should_power_cycle():
    """Check if power cycling is enabled (all parameters not zero)"""
    config = get_mb_power_config()
    return (config["atx_on"] > 0 or config["atx_off"] > 0 or 
            config["ltm_on"] > 0 or config["ltm_off"] > 0)

def update_atx_power_state(current_time):
    """Update ATX power state based on timing configuration"""
    global atx_power_state, atx_timer_start
    
    config = get_mb_power_config()
    
    # If all parameters are 0, keep ATX always on
    if config["atx_on"] == 0 and config["atx_off"] == 0:
        atx_power_state = True
        return True
    
    # Calculate elapsed time since last state change
    elapsed = current_time - atx_timer_start
    
    if atx_power_state:
        # ATX is currently ON, check if it's time to turn OFF
        if elapsed >= config["atx_on"]:
            atx_power_state = False
            atx_timer_start = current_time
            cprint("ATX power OFF")
    else:
        # ATX is currently OFF, check if it's time to turn ON
        if elapsed >= config["atx_off"]:
            atx_power_state = True
            atx_timer_start = current_time
            cprint("ATX power ON")
    
    return atx_power_state

def update_ltm_power_state(current_time):
    """Update LTM power state based on timing configuration"""
    global ltm_power_state, ltm_timer_start
    
    config = get_mb_power_config()
    
    # If all parameters are 0, keep LTM always on
    if config["ltm_on"] == 0 and config["ltm_off"] == 0:
        ltm_power_state = True
        return True
    
    # LTM only operates when ATX is ON
    if not atx_power_state:
        ltm_power_state = False
        return False
    
    # Calculate elapsed time since last state change
    elapsed = current_time - ltm_timer_start
    
    if ltm_power_state:
        # LTM is currently ON, check if it's time to turn OFF
        if elapsed >= config["ltm_on"]:
            ltm_power_state = False
            ltm_timer_start = current_time
            # cprint("LTM power OFF")
    else:
        # LTM is currently OFF, check if it's time to turn ON
        if elapsed >= config["ltm_off"]:
            ltm_power_state = True
            ltm_timer_start = current_time
            # cprint("LTM power ON")
    
    return ltm_power_state

def initialize_power_control(current_time):
    """Initialize power control timers"""
    global atx_timer_start, ltm_timer_start
    atx_timer_start = current_time
    ltm_timer_start = current_time


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
v_12v_cal = 3300. / (3300. + 15000.)
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