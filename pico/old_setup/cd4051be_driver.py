from machine import Pin
import time

class CD4051BE:
    def __init__(self, a, b, c, en=None):
        """
        CD4051BE 8-channel analog multiplexer/demultiplexer
        
        Args:
            a, b, c: Control pins (A, B, C) - these select the channel
            en: Enable pin (optional, active LOW) - if not provided, chip is always enabled
        """
        self.select_pins = [
            Pin(a, Pin.OUT),
            Pin(b, Pin.OUT), 
            Pin(c, Pin.OUT)
        ]
        self.en = Pin(en, Pin.OUT) if en is not None else None
        
        if self.en:
            self.enable()  # start enabled

    def enable(self):
        """Enable the multiplexer (active LOW)"""
        if self.en:
            self.en.value(0)

    def disable(self):
        """Disable the multiplexer"""
        if self.en:
            self.en.value(1)

    def select_channel(self, channel):
        """Select one of the 8 channels (0-7)"""
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0-7")
        
        # Convert channel number to binary and set control pins
        bits = [(channel >> i) & 1 for i in range(3)]
        for pin, bit in zip(self.select_pins, bits):
            pin.value(bit)

    def channel_to_bits(self, channel):
        """Return the binary representation for a given channel (for debugging)"""
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0-7")
        return [(channel >> i) & 1 for i in range(3)]

    def get_channel_table(self):
        """Print the truth table for channel selection"""
        print("CD4051BE Channel Selection:")
        print("Channel | C B A")
        print("----------------")
        for channel in range(8):
            bits = self.channel_to_bits(channel)
            print(f"   {channel}    | {bits[2]} {bits[1]} {bits[0]}")