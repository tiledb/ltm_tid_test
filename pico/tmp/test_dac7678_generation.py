from machine import Pin, I2C
import math
import time
import urandom  # MicroPython random

# I2C setup
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
DAC7678_ADDR = 0x4C  # Replace with your device address (based on A0 pin)

# Base command codes
CMD_WRITE_INPUT = 0b00000000
CMD_UPDATE_DAC = 0b00010000
CMD_WRITE_UPDATE = 0b00110000
CMD_BROADCAST_WRITE = 0b00001111
CMD_BROADCAST_UPDATE = 0b00011111

# Register read pointer (Input register read is 0b10000000 | channel)
CMD_READ_INPUT_BASE = 0b10000000

def write_input(channel, value):
    """Write 12-bit value to input register (does NOT update output)."""
    _send_data(CMD_WRITE_INPUT | (channel & 0x07), value)

def update_output(channel):
    """Trigger update of DAC output register for a channel."""
    cmd = CMD_UPDATE_DAC | (channel & 0x07)
    i2c.writeto(DAC7678_ADDR, bytes([cmd, 0x00, 0x00]))

def write_and_update(channel, value):
    """Write 12-bit value to input register and update DAC output."""
    _send_data(CMD_WRITE_UPDATE | (channel & 0x07), value)

def broadcast_write(value):
    """Write the same value to all input registers."""
    _send_data(CMD_BROADCAST_WRITE, value)

def broadcast_update():
    """Update all DAC output registers from input registers."""
    i2c.writeto(DAC7678_ADDR, bytes([CMD_BROADCAST_UPDATE, 0x00, 0x00]))

def read_input(channel):
    """Read back the input register (12-bit) for a specific channel (0–7)."""
    if not (0 <= channel <= 7):
        raise ValueError("Channel must be 0–7")
    read_cmd = CMD_READ_INPUT_BASE | (channel & 0x07)
    i2c.writeto(DAC7678_ADDR, bytes([read_cmd]))  # Set read pointer
    data = i2c.readfrom(DAC7678_ADDR, 2)
    high = data[0]
    low = data[1] >> 4
    value = (high << 4) | low
    return value

def _send_data(cmd, value):
    """Send 3-byte command to DAC7678 with 12-bit value."""
    value = max(0, min(4095, value))  # Clamp value
    if not (0 <= value <= 0xFFF):
        raise ValueError("Value must be 0–4095")
    high_byte = (value >> 4) & 0xFF
    low_byte = (value & 0x0F) << 4
    i2c.writeto(DAC7678_ADDR, bytes([cmd, high_byte, low_byte]))


# === Waveform generator ===
def generate_waveforms(duration_s=10, sample_rate=100):
    """
    Generate different waveforms on each DAC channel for a certain duration.
    """
    samples = int(duration_s * sample_rate)
    delay = 1.0 / sample_rate
    for i in range(samples):
        t = i / 100 * 2 * math.pi  # normalized time [0, 2π]

        # Values between 0–4095
        sine_val = int((math.sin(t) + 1) * 2047.5)
        print(sine_val)
        triangle_val = int(4095 * (2 / math.pi * math.asin(math.sin(t))))
        square_val = 4095 if math.sin(t) > 0 else 0
        saw_val = int((t % (2*math.pi)) / (2*math.pi) * 4095)
        inv_saw = 4095 - saw_val
        pulse = 4095 if (i % 20 == 0) else 0
        step = (i % 8) * 512
        noise = urandom.getrandbits(12)

        # Write waveforms to DAC channels A–H
        write_and_update(0, sine_val)      # A
        write_and_update(1, triangle_val)  # B
        write_and_update(2, square_val)    # C
        write_and_update(3, saw_val)       # D
        write_and_update(4, inv_saw)       # E
        write_and_update(5, pulse)         # F
        write_and_update(6, step)          # G
        write_and_update(7, noise)         # H

        time.sleep(delay)

# === Run demo ===
generate_waveforms(duration_s=1000, sample_rate=1000)

# === Example usage ===

# Write and update channel C (2) to 3000
write_and_update(2, 3000)

# Write to D (3) input, but update later
write_input(3, 1234)
time.sleep(0.1)
update_output(3)

# Broadcast all to 2048
broadcast_write(2048)
broadcast_update()

# Read back value of channel B (1)
val = read_input(1)
print("Channel B input register =", val)
