from machine import Pin

class MCP4151:
    def __init__(self, spi, cs_pin):
        """
        Initialize MCP4151 digital potentiometer
        
        Args:
            spi: Initialized SPI bus instance (from machine.SPI)
            cs_pin: GPIO pin number for Chip Select (active low)
        
        Example:
            from machine import SPI, Pin
            spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=Pin(0), mosi=Pin(1), miso=Pin(2))
            pot = MCP4151(spi, cs_pin=3)
        """
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT)
        self.cs.value(1)  # Deselect chip initially
        
    def set_resistance(self, value):
        """
        Set the wiper position (0-255)
        
        Args:
            value: 8-bit value (0-255) for wiper position
                  0 = minimum resistance
                  255 = maximum resistance
        
        Returns:
            None
        """
        # Ensure value is within valid range
        value = max(0, min(255, value))
        
        # MCP4151 command format:
        # First byte: Command (0x00 for write to wiper)
        # Second byte: Data (wiper value)
        cmd = bytearray([0x00, value])
        
        self.cs.value(0)  # Select chip
        self.spi.write(cmd)
        self.cs.value(1)  # Deselect chip
    
    def increment(self, steps=1):
        """
        Increment the wiper position
        
        Args:
            steps: Number of steps to increment (default 1)
        """
        current = self.get_resistance()
        self.set_resistance(min(255, current + steps))
    
    def decrement(self, steps=1):
        """
        Decrement the wiper position
        
        Args:
            steps: Number of steps to decrement (default 1)
        """
        current = self.get_resistance()
        self.set_resistance(max(0, current - steps))
    
    def get_resistance(self):
        """
        Read the current wiper position
        
        Returns:
            Current wiper position (0-255)
        """
        # Command format for reading:
        # 0x0C - read wiper position
        cmd = bytearray([0x0C, 0x00])
        response = bytearray(2)
        
        self.cs.value(0)
        self.spi.write_readinto(cmd, response)
        self.cs.value(1)
        
        return response[1]
    
    def set_resistance_percent(self, percent):
        """
        Set resistance as a percentage of full scale
        
        Args:
            percent: 0-100 value representing percentage of full scale
        """
        value = int(percent * 2.55)
        self.set_resistance(value)