"""
LTM Multi-Channel Control Library for Raspberry Pi Pico
General-purpose MicroPython library for controlling any number of DC-DC 
converter enable pins (LTM modules).

Author: Piro
Version: 1.0
"""

from machine import Pin
import time


class ltm_run:
    """
    General-purpose control class for an arbitrary number of digital output pins.

    Features:
    - Any number of channels
    - Active-low or active-high logic
    - on/off/toggle/state
    - all_on/all_off/all_toggle
    - pulse and sequence functions
    """

    def __init__(self, pin_list, active_low=True):
        """
        Initialize the LTM control class.

        Args:
            pin_list (list[int]): List of GPIO pin numbers to control.
            active_low (bool): Whether outputs are active-low.
        """
        if not isinstance(pin_list, list) or len(pin_list) == 0:
            raise ValueError("pin_list must be a non-empty list of GPIO pins")

        self.active_low = active_low
        self.channels = []

        for pin_number in pin_list:
            pin = Pin(pin_number, Pin.OUT)
            self.channels.append(pin)

        # Turn everything off initially
        self.all_off()

        print(f"LTMControl initialized with {len(pin_list)} channels: {pin_list}")

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def _validate_channel(self, channel):
        if not (1 <= channel <= len(self.channels)):
            raise ValueError(f"Channel must be between 1 and {len(self.channels)}")

    def _state_value(self, desired_on):
        """Convert logical ON/OFF to actual pin level."""
        if self.active_low:
            return 0 if desired_on else 1
        else:
            return 1 if desired_on else 0

    # ---------------------------------------------------------
    # Individual Channel Actions
    # ---------------------------------------------------------
    def on(self, channel):
        """Turn ON a specific channel."""
        self._validate_channel(channel)
        self.channels[channel - 1].value(self._state_value(True))

    def off(self, channel):
        """Turn OFF a specific channel."""
        self._validate_channel(channel)
        self.channels[channel - 1].value(self._state_value(False))

    def toggle(self, channel):
        """Toggle a specific channel."""
        self._validate_channel(channel)
        pin = self.channels[channel - 1]
        pin.value(1 - pin.value())

    def state(self, channel):
        """
        Get current ON/OFF state of a channel.
        Returns True if ON, False if OFF.
        """
        self._validate_channel(channel)
        raw = self.channels[channel - 1].value()

        if self.active_low:
            return raw == 0
        else:
            return raw == 1

    # ---------------------------------------------------------
    # Group Actions
    # ---------------------------------------------------------
    def all_on(self):
        """Turn ON all channels."""
        target = self._state_value(True)
        for pin in self.channels:
            pin.value(target)

    def all_off(self):
        """Turn OFF all channels."""
        target = self._state_value(False)
        for pin in self.channels:
            pin.value(target)

    def all_toggle(self):
        """Toggle all channels."""
        for pin in self.channels:
            pin.value(1 - pin.value())

    # ---------------------------------------------------------
    # Advanced Functions
    # ---------------------------------------------------------
    def pulse(self, channel, duration_ms=1000):
        """
        Pulse a channel ON for a given time.

        Args:
            channel (int)
            duration_ms (int)
        """
        self.on(channel)
        time.sleep_ms(duration_ms)
        self.off(channel)

    def sequence(self, channels, delay_ms=500):
        """
        Activate channels one-by-one in a sequence.

        Args:
            channels (list[int]): Channels to run in order.
            delay_ms (int)
        """
        for channel in channels:
            self._validate_channel(channel)
            self.on(channel)
            time.sleep_ms(delay_ms)
            self.off(channel)

    # ---------------------------------------------------------
    # Optional: Built-in hardware test
    # ---------------------------------------------------------
    def test(self):
        print("Running LTM channel test...")

        # Individual on/off
        for i in range(1, len(self.channels) + 1):
            print(f"Channel {i} ON")
            self.on(i)
            time.sleep(0.5)
            print(f"Channel {i} OFF")
            self.off(i)
            time.sleep(0.5)

        # Toggle all
        print("Toggling all channels...")
        self.all_toggle()
        time.sleep(1)
        self.all_toggle()
        time.sleep(1)

        # Pulse first channel
        print("Pulsing channel 1...")
        self.pulse(1, 500)

        # Sequence test
        print("Running sequence...")
        self.sequence(list(range(1, len(self.channels) + 1)), 300)

        print("Test complete!")
