from cd74hc4067_driver import CD74HC4067
import time

mux = CD74HC4067(s0=21, s1=20, s2=19, s3=18)

mux.select_channel(15)

# for ch in range(16):
#     mux.select_channel(ch)
#     print(f"Channel {ch}")
#     time.sleep(5)  # Wait for 1 second before switching to the next channel
    
