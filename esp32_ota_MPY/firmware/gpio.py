import esp32
import machine
from machine import Pin, Timer
import utime
from mqtt import*

# Pin Setup
R1 = Pin(26, Pin.OUT)
R2 = Pin(25, Pin.OUT)
R3 = Pin(33, Pin.OUT)

S_Led = Pin(4, Pin.OUT)

F1 = Pin(17, Pin.IN, Pin.PULL_DOWN)
F2 = Pin(18, Pin.IN, Pin.PULL_DOWN)
F3 = Pin(19, Pin.IN, Pin.PULL_DOWN)

Rst = Pin(32, Pin.IN, Pin.PULL_UP)

# Globals
last_trigger_times = {"F1": 0, "F2": 0, "F3": 0}
press_start_time = None
DEBOUNCE_DELAY = 400
debounce_timer = Timer(2)
reset_timer = Timer(1)

    
def http_server_led():
    S_Led.value(1)
    time.sleep(1)
    S_Led.value(0)
    time.sleep(1)
    S_Led.value(1)
    time.sleep(1)
    S_Led.value(0)
    time.sleep(1)
    S_Led.value(1)
    time.sleep(1)
    S_Led.value(0)
    time.sleep(1)



