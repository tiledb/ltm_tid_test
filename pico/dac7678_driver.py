from machine import Pin, I2C
import math
import time
import urandom  # MicroPython random

# Base command codes
CMD_WRITE_INPUT = 0b00000000
CMD_UPDATE_DAC = 0b00010000
CMD_WRITE_UPDATE = 0b00110000
CMD_BROADCAST_WRITE = 0b00001111
CMD_BROADCAST_UPDATE = 0b00011111
CMD_READ_INPUT_BASE = 0b00000000  # Input register read is 0b10000000 | channel

class DAC7678:
    def __init__(self, i2c, address=0x4C, vref=3.3, verbose=False):
        """
        Initialize DAC7678 controller.
        
        Args:
            i2c: Initialized I2C interface
            address: I2C address of the DAC (default 0x4C)
            vref: Reference voltage for voltage calculations (default 3.3V)
            verbose: Print debug information (default False)
        
        Raises:
            ValueError: If device not found at specified address
            TypeError: If i2c is not initialized properly
        """
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an initialized I2C interface")
            
        self.i2c = i2c
        self.address = address
        self.vref = float(vref)
        self.verbose = verbose
        
        # Verify device is present
        devices = self.i2c.scan()
        if self.address not in devices:
            raise ValueError(f"No DAC7678 found at address 0x{self.address:02X} (found: {[hex(d) for d in devices]})")

    @property
    def resolution(self):
        """Return voltage resolution per LSB step."""
        return self.vref / 4095

    def write_input(self, channel, value):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0–7")
        self._send_data(CMD_WRITE_INPUT | (channel & 0x07), value)

    def update_output(self, channel):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0–7")
        cmd = CMD_UPDATE_DAC | (channel & 0x07)
        self.i2c.writeto(self.address, bytes([cmd, 0x00, 0x00]))

    def write_and_update(self, channel, value):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0–7")
        self._send_data(CMD_WRITE_UPDATE | (channel & 0x07), value)

    def broadcast_write(self, value):
        self._send_data(CMD_BROADCAST_WRITE, value)

    def broadcast_update(self):
        self.i2c.writeto(self.address, bytes([CMD_BROADCAST_UPDATE, 0x00, 0x00]))

    def read_input(self, channel):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0–7")

        try:
            read_cmd = CMD_READ_INPUT_BASE | (channel & 0x07)
            self.i2c.writeto(self.address, bytes([read_cmd]))  # Remove stop=False
            time.sleep_us(50)  # Short delay to allow device to prepare data
            data = self.i2c.readfrom(self.address, 2)
            high = data[0]
            low = (data[1] & 0xF0) >> 4
            return (high << 4) | low
        except OSError as e:
            raise RuntimeError(f"I2C read failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during read: {e}")
        
    def set_voltage(self, channel, voltage):
        if voltage < 0 or voltage > self.vref:
            raise ValueError(f"Voltage must be between 0 and {self.vref}V")
        value = int((voltage / self.vref) * 4095)
        value = max(0, min(4095, value))
        self.write_and_update(channel, value)
        return value

    def write_all_channels(self, values):
        """
        Write values to all 8 channels, then broadcast update.
        Args:
            values (list[int]): List of 8 integers (0–4095)
        """
        if len(values) != 8:
            raise ValueError("Exactly 8 values required.")
        for i, val in enumerate(values):
            self.write_input(i, val)
        self.broadcast_update()

    def _send_data(self, cmd, value):
        if not 0 <= value <= 4095:
            raise ValueError("Value must be 0–4095")
        high_byte = (value >> 4) & 0xFF
        low_byte = (value & 0x0F) << 4
        self.i2c.writeto(self.address, bytes([cmd, high_byte, low_byte]))

    def generate_waveforms(self, duration_s=10, sample_rate=100):
        samples = int(duration_s * sample_rate)
        delay = max(0, 1.0 / sample_rate)
        twopi = 2 * math.pi

        try:
            if self.verbose:
                print(f"=== Generating waveforms for {duration_s}s at {sample_rate} Hz ===")
            for i in range(samples):
                t = i / sample_rate * twopi

                waveforms = [
                    int((math.sin(t) + 1) * 2047.5),                              # Sine
                    int(((2 / math.pi) * math.asin(math.sin(t)) + 1) * 2047.5), # Triangle
                    4095 if math.sin(t) > 0 else 0,                              # Square
                    int((t % twopi) / twopi * 4095),                             # Sawtooth
                    4095 - int((t % twopi) / twopi * 4095),                      # Inverted Sawtooth
                    4095 if (i % 20 == 0) else 0,                                # Pulse
                    (i % 8) * 585,                                               # Step
                    urandom.getrandbits(12) & 0xFFF                              # Noise
                ]

                for channel, raw_value in enumerate(waveforms):
                    value = max(0, min(4095, raw_value))
                    if self.verbose:
                        print(f"Ch{channel}: {value:4d} ({value/4095*self.vref:.2f}V)")
                    try:
                        self.write_and_update(channel, value)
                    except Exception as e:
                        print(f"Error updating channel {channel} with value {value}: {e}")

                time.sleep(delay)

            if self.verbose:
                print("=== Waveform generation complete ===")

        except KeyboardInterrupt:
            print("=== Waveform generation interrupted by user ===")
        except Exception as e:
            raise RuntimeError(f"Waveform generation failed: {e}")

    def reset(self):
        try:
            self.broadcast_write(0)
            self.broadcast_update()
        except OSError as e:
            raise RuntimeError(f"I2C error during reset: {e}")
        except Exception as e:
            raise RuntimeError(f"Reset failed: {e}")

    def __repr__(self):
        return f"DAC7678(i2c={self.i2c}, address=0x{self.address:02X}, vref={self.vref}V)"


# Optional quick test/demo block for MicroPython
if __name__ == "__main__":
    try:
        i2c = I2C(1, scl=Pin(22), sda=Pin(21))  # Adjust for your board
        dac = DAC7678(i2c, vref=3.3, verbose=True)

        print("DAC resolution: {:.6f} V/step".format(dac.resolution))

        print("Setting channel 0 to 1.65V...")
        actual_val = dac.set_voltage(0, 1.65)
        print(f"Raw value sent: {actual_val}")

        print("Reading back input register for channel 0...")
        print("Raw value read:", dac.read_input(0))

        print("Running waveform generator...")
        dac.generate_waveforms(duration_s=5, sample_rate=50)

        print("Resetting all channels to 0...")
        dac.reset()

    except Exception as e:
        print("Demo failed:", e)
