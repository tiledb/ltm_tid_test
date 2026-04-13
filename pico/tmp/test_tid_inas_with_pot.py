from machine import Pin, SPI, I2C
import time

# Import your drivers (make sure they are on the Pico)
from cd74hc4067_driver import CD74HC4067
from dac7678_driver import DAC7678
from mcp3208_driver import MCP3208
from mcp4151_driver import MCP4151

# Initialize the MUX (CD74HC4067)
mux = CD74HC4067(s0=21, s1=20, s2=19, s3=18)

# Initialize the DAC (DAC7678)
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
dac = DAC7678(i2c)

# Initialize the ADC (MCP3208)
spi_adc = SPI(0, baudrate=400000, polarity=0, phase=0,
             sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs_adc = Pin(5, Pin.OUT)
adc = MCP3208(spi_adc, cs_adc)

# Initialize the Digital Potentiometer (MCP4151)
spi_pot = SPI(1, baudrate=1000000, polarity=0, phase=0,
             sck=Pin(14), mosi=Pin(15), miso=Pin(12))
cs_pot = Pin(13, Pin.OUT)
pot = MCP4151(spi_pot, cs_pot)

# Target potentiometer values (0-255 for 256 divisions)
# pot_values_ohm = [855, 466, 320, 244, 197]
gain_values = [25, 50, 100, 150, 1000]

print("Gain settings:", gain_values)
pot_values_ohm = [int(1+(100000/gain_values[g])) for g in range(len(gain_values))]  # Adjust for gain

print("Potentiometer values (Ohm):", pot_values_ohm)
# pot_values_ohm = [197, 244, 320, 466, 855]
pot_values = [int(255- (value / 5000) * 255) for value in pot_values_ohm]  # Convert to 0-255 scale

mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 0, 0, 0, 10, 11, 12, 13, 14, 15]
mux_nr_of_channels = 20 #16


ina_lot = ["dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380309b", 
               "dmz380307", 
               "dmz380307", 
               "dmz380307", 
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307",
               "dmz380307"]

ina_label = ["41",
                 "42",
                 "101",
                 "44",
                 "45",
                 "46",
                 "47",
                 "48",
                 "49",
                 "50",
                 "21",
                 "22",
                 "23",
                 "24",
                 "25",
                 "26",
                 "27",
                 "28",
                 "29",
                 "30"]




# DAC sweep range (0-4095 for 12-bit DAC)
dac_min = 0
dac_max = 4095
dac_step = 100  # Adjust this for finer/coarser sweep

def main():
    print("Starting DAC sweep with fixed potentiometer values...")
    print("Format: Pot_Value, DAC_Value, ADC_Reading")
    print("-" * 40)
    
    for pot_value in pot_values:
        # Set the digital potentiometer
        try:
            pot.set_resistance(pot_value)
            print(f"Potentiometer set to: {pot_value}")
            time.sleep(1)  # Allow settling time
        except Exception as e:
            print(f"Error setting pot to {pot_value}: {e}")
            continue
        
        # Sweep through all DAC values
        for dac_value in range(dac_min, dac_max + 1, dac_step):
            try:
                # Set DAC output
                dac.write_and_update(0, dac_value)
                dac_readback = dac.read_input(0)
                time.sleep(0.01)  # Short settling time
                
                # Read from ADC
                adc_reading = adc.read_channel(0)  # Read channel 0
                
                # Print results
                # print(f"{pot_value}, {dac_readback}, {adc_reading}")
                
            except Exception as e:
                print(f"Error at DAC value {dac_value}: {e}")
        
        time.sleep(3)
        print("-" * 40)  # Separator between potentiometer values
    
    print("Sweep complete!")

if __name__ == "__main__":
    main()