from machine import I2C

class Encoder:
    """
    AS5048B magnetic encoder
    https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf
    """
    resolution = 16384  # 14 bits
    half = 16384 / 2
    angle_register = int(0xFE)
    auto_gain_control_reg = int(0xFA)
    diagnostics_reg = int(0xFB)
    zero_reg = int(0x16)

    def __init__(self, name: str, address: int, invert: bool, offset: int, i2c: I2C):
        self.name = name
        self.address = address
        self.ring_size = 8
        self.ring = [0] * self.ring_size
        self.index = 0
        self.invert = invert
        self.offset = offset
        self.i2c = i2c

    def chk(self) -> None:
        high, low = list(self.i2c.readfrom_mem(self.address, self.angle_register, 2))  # read from device
        self.index = (self.index + 1) % self.ring_size  # count around ring averager

        ang = (high << 6) + low - self.offset
        if ang > self.half:
            ang = ang - self.resolution
        self.ring[self.index] = ang  # add new value to ring

    @property
    def state(self):
        if self.invert:
            return -int(sum(self.ring) / self.ring_size)  # average ring buffer and invert
        return int(sum(self.ring) / self.ring_size)

    @property
    def angle(self):
        return self.state / self.resolution * 360.0

    def get_gain(self):
        """ 255 is low field 0 is high field """
        return self.i2c.readfrom_mem(self.address, self.auto_gain_control_reg, 1)[0]

    def get_diag(self):
        raw = self.i2c.readfrom_mem(self.address, self.diagnostics_reg, 1)[0]
        return {'mag too low': bool(raw & 8),
                'mag too high': bool(raw & 4),
                'CORDIC Overflow': bool(raw & 2),
                'Offset Compensation finished': bool(raw & 1)
                }

    def set_zero(self):
        pos = self.i2c.readfrom_mem(self.address, self.angle_register, 2)
        utime.sleep_ms(10)
        self.i2c.writeto_mem(self.address, self.zero_reg, pos)