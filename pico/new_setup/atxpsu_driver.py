from machine import Pin
import time

class atxpsu:
    def __init__(self, ps_on_pin, power_good_pin=None, delay_ms=500, invert_polarity=False):
        """
        ATX Power Supply Controller
        
        Args:
            ps_on_pin: Pin connected to MOSFET gate
            power_good_pin: Optional pin to read PWR_OK signal
            delay_ms: Delay after power on/off for stabilization (default: 500ms)
            invert_polarity: If True, invert the polarity of both PS_ON and PWR_OK signals
        """
        self.ps_on = Pin(ps_on_pin, Pin.OUT)
        self.power_good = Pin(power_good_pin, Pin.IN) if power_good_pin else None
        self.delay_ms = delay_ms
        self.invert_polarity = invert_polarity
        
        # Start with power supply OFF
        # Apply polarity inversion to initial state
        off_state = 0 if self.invert_polarity else 1
        self.ps_on.value(off_state)
        self._state = False
        
        # Allow time for power supply to initialize
        time.sleep_ms(100)

    def _get_ps_on_state(self, power_on):
        """
        Convert power state to appropriate GPIO level with polarity consideration
        
        Args:
            power_on: Boolean indicating desired power state (True=ON, False=OFF)
        
        Returns:
            GPIO level (0 or 1) with polarity applied
        """
        if self.invert_polarity:
            return 0 if power_on else 1  # Inverted: ON=LOW, OFF=HIGH
        else:
            return 1 if power_on else 0  # Normal: ON=HIGH, OFF=LOW

    def _get_power_good_state(self, gpio_value):
        """
        Convert GPIO reading to power good state with polarity consideration
        
        Args:
            gpio_value: Raw GPIO value (0 or 1)
        
        Returns:
            Boolean indicating if power is good
        """
        if self.invert_polarity:
            return gpio_value == 0  # Inverted: Good=LOW
        else:
            return gpio_value == 1  # Normal: Good=HIGH

    def power_on(self):
        """Turn ON the ATX power supply"""
        gpio_level = self._get_ps_on_state(True)
        self.ps_on.value(gpio_level)
        self._state = True
        time.sleep_ms(self.delay_ms)
        
        polarity_status = " (inverted polarity)" if self.invert_polarity else ""
        print(f"ATX Power Supply: ON{polarity_status}")
        
        if self.power_good:
            # Wait for power good signal with timeout
            timeout = 5000  # 5 second timeout
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
                raw_value = self.power_good.value()
                power_good_state = self._get_power_good_state(raw_value)
                
                if power_good_state:
                    print("Power Good signal detected")
                    return True
                time.sleep_ms(100)
            print("Warning: Power Good signal not detected within timeout")
            return False
        return True

    def power_off(self):
        # Apply polarity to determine correct GPIO level
        gpio_level = self._get_ps_on_state(False)
        self.ps_on.value(gpio_level)
        self._state = False
        time.sleep_ms(self.delay_ms)
        
        polarity_status = " (inverted polarity)" if self.invert_polarity else ""
        print(f"ATX Power Supply: OFF{polarity_status}")
        return True

    def toggle(self):
        """Toggle power state"""
        if self._state:
            return self.power_off()
        else:
            return self.power_on()

    def get_state(self):
        """Get current power state"""
        return self._state

    def is_power_good(self):
        """Check if power good signal is present (if available)"""
        if self.power_good:
            raw_value = self.power_good.value()
            return self._get_power_good_state(raw_value)
        return None

    def soft_power_cycle(self, off_time_ms=3000):
        """
        Perform a soft power cycle (off -> wait -> on)
        
        Args:
            off_time_ms: Time to keep power off before turning back on
        """
        print(f"Performing power cycle (off for {off_time_ms}ms)")
        self.power_off()
        time.sleep_ms(off_time_ms)
        return self.power_on()

    def get_polarity_mode(self):
        """Get current polarity configuration"""
        return "inverted" if self.invert_polarity else "normal"