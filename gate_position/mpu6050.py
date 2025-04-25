from machine import I2C, Pin
from time import ticks_ms, ticks_diff, sleep_ms
from math import atan2, pi

MPU_ADDR = 0x68

class MPU6050Swing:
    def __init__(self, i2c):
        self.i2c = i2c
        self.offsetGyroZ = 0
        self.fusedAngleZ = 0
        self.lastTime = ticks_ms()

        # Wake up MPU6050
        self.i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')

    def read_raw_data(self):
        data = self.i2c.readfrom_mem(MPU_ADDR, 0x3B, 14)
        ax = self._combine(data[0], data[1])
        ay = self._combine(data[2], data[3])
        az = self._combine(data[4], data[5])
        gx = self._combine(data[8], data[9])
        gy = self._combine(data[10], data[11])
        gz = self._combine(data[12], data[13])
        return ax, ay, az, gx, gy, gz

    def _combine(self, high, low):
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 65536
        return value

    def calibrate_gyro_z(self, samples=200):
        print("Calibrating gyro Z...")
        total = 0
        for _ in range(samples):
            _, _, _, _, _, gz = self.read_raw_data()
            total += gz
            sleep_ms(5)
        self.offsetGyroZ = (total / samples) / 131.0
        print("Gyro Z offset:", self.offsetGyroZ)

    def update(self):
        now = ticks_ms()
        deltaTime = ticks_diff(now, self.lastTime) / 1000.0
        self.lastTime = now

        ax, ay, _, _, _, gz = self.read_raw_data()

        accAngleZ = atan2(ay, ax) * 180 / pi
        gyroRateZ = (gz / 131.0) - self.offsetGyroZ

        self.fusedAngleZ = 0.96 * (self.fusedAngleZ + gyroRateZ * deltaTime) + 0.04 * accAngleZ
        swingAngle = min(max(self.fusedAngleZ, 0), 110)
        openPercent = (swingAngle / 110.0) * 100.0

        return swingAngle, openPercent

