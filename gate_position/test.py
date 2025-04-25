from machine import Pin, I2C
from time import sleep
from mpu6050 import MPU6050Swing

i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust pins if needed
mpu = MPU6050Swing(i2c)

mpu.calibrate_gyro_z()

while True:
    angle, percent = mpu.update()
    print("Swing Angle: {:.2f}°, Open %: {:.2f}%".format(angle, percent))
    sleep(0.2)

