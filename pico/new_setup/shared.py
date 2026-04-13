import _thread

cprint_enabled = False
nprint_enabled = False
delimiter_line = "=========="

stop_data_task = False


def cprint(msg):
    if shared.cprint_enabled:
        try:
            print("--" + msg + "--")
        except OSError:
            pass
def nprint(msg):
    if shared.nprint_enabled:
        try:
            print(msg)
        except OSError:
            pass



ltm_lot = ["4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4", 
           "4581637ml4", "4581637ml4", "4581637ml4",  "4581637ml4"]

ltm_label = ["1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
            "1",             "2",             "3",             "4",             "5",             "6",             "7",             "8",
             "10",             "11",             "12",             "13"]



nr_of_channels = 27
mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, # 13, 14, 15,
          0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,   #, 13, 14, 15
          13
            ]

output_adc_ch = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,# 1, 1, 1
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,# 0, 0, 0,
                4
                ]

output_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, #, 0, 0, 0
                    0
                    
                        ]

output_adc_value_avg = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, #, 0, 0, 0
                        0
                        ]


output_adc_value_v = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, #, 0, 0, 0
                        0
                        ]


output_adc_value_min = [1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8,
                        1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8,
                        0
                        ]

output_adc_value_max = [1.3, 5.1, 1.6, 3.4, 5.1, 5.1, 5.1, 5.1, 5.1, 2.6, 1.7, 1.1, 1.,
                        1.1, 4.9, 1.4, 3.2, 1., 1., 1., 1., 4.9, 2.4, 1.9, 0.9, 0.8,
                        3.3
                        ]



output_adc_value_min_test = [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5,
                        -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5,
                        -0.5
                        ]

output_adc_value_max_test = [5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5,
                        5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5,
                        5.5
                        ]



adc_resolution = 4096  # 12-bit ADC
adc_reference_voltage = 3.3  # Reference voltage for ADC in volts
adc_cal = adc_reference_voltage / adc_resolution  # Volts per ADC count

pg_x_cal = 47000. / (47000. + 47000.)
pg_12v_cal = 47000. / (47000. + 47000.)
v_x_cal = 1000. / (1000. + 1000.)
v_12v_cal = 3300. / (3300. + 8200.)
c_x_cal = 12000./100.


output_adc_value_v_calibration_factor =[v_x_cal, pg_x_cal, c_x_cal, pg_x_cal, v_x_cal, pg_x_cal, c_x_cal, c_x_cal, c_x_cal, v_x_cal, v_x_cal, c_x_cal,  v_x_cal,
                c_x_cal, v_x_cal, v_12v_cal, v_x_cal, c_x_cal, v_x_cal, pg_x_cal, pg_x_cal, v_x_cal, c_x_cal, c_x_cal, v_x_cal,  c_x_cal,
                pg_12v_cal
                ]



channel_label = ["v_e1", "pg_e", "c_e1", "pg_d", "v_e2", "pg_c", "c_e2", "c_d1", "c_d2", "v_d1", "v_d2", "c_c1",  "v_c1",
                "c_c2", "v_c2", "v_12v", "v_b1", "c_b1", "v_b2", "pg_b", "pg_a", "v_a1", "c_b2", "c_a1", "v_a2",  "c_a2",
                "pg_12v"
                ]









data_lock = _thread.allocate_lock()
