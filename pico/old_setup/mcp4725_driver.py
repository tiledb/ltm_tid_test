from machine import I2C
import time

class MCP4725:
    # Base I2C address (A2:A0 configurable, default A0=0)
    BASE_ADDR = 0x60

    # Write modes
    CMD_FAST_MODE = 0x00           # C2,C1 = 00 (Fast mode)
    CMD_WRITE_DAC = 0x40           # C2,C1,C0 = 010
    CMD_WRITE_DAC_EEPROM = 0x60    # C2,C1,C0 = 011

    def __init__(self, i2c: I2C, address: int = BASE_ADDR):
        self.i2c = i2c
        self.address = address

    def write_fast(self, value):
        """Fast mode write (no EEPROM)"""
        value = min(4095, max(0, value))  # Clamp to 12-bit
        upper = (value >> 4) & 0xFF
        lower = (value & 0x0F) << 4
        self.i2c.writeto(self.address, bytes([upper, lower]))

    def write_dac(self, value):
        """Standard mode: write DAC only (no EEPROM)"""
        value = min(4095, max(0, value))
        cmd = self.CMD_WRITE_DAC
        data = [
            cmd,                      # Command byte
            (value >> 4) & 0xFF,      # Upper data byte
            (value & 0x0F) << 4       # Lower data byte
        ]
        self.i2c.writeto(self.address, bytes(data))

    def write_dac_eeprom(self, value):
        """Standard mode: write DAC + EEPROM"""
        value = min(4095, max(0, value))
        cmd = self.CMD_WRITE_DAC_EEPROM
        data = [
            cmd,                      # Command byte
            (value >> 4) & 0xFF,      # Upper data byte
            (value & 0x0F) << 4       # Lower data byte
        ]
        self.i2c.writeto(self.address, bytes(data))
        # EEPROM write delay (~25ms typical)
        time.sleep_ms(30)

    def read(self):
        """Read current DAC & EEPROM values"""
        self.i2c.writeto(self.address, b"", stop=False)
        data = self.i2c.readfrom(self.address, 5)

        dac_value = ((data[1] & 0x0F) << 8) | data[2]
        eeprom_value = (data[3] << 4) | (data[4] >> 4)

        rdy = (data[1] >> 7) & 0x01
        return {
            "dac": dac_value,
            "eeprom": eeprom_value,
            "ready": bool(rdy)
        }
