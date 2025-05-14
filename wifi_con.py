import esp32
import machine
import urandom
import network
import usocket
import usocket as socket
import uasyncio as asyncio
import time
import utime
import ubinascii
from nvs import get_stored_wifi_credentials
from time import sleep_ms
from machine import Timer
from nvs import get_product_id, product_key, product_id
from gpio import S_Led

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.config(dhcp_hostname=product_id)
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=f"onwords-{product_id}", authmode=network.AUTH_OPEN)

while ap.active() is False:
    time.sleep(1)
print("AP Mode Active. IP Address:", ap.ifconfig()[0])



async def connect_wifi(ssid, password, max_retries=5):
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt+1} to connect Wi-Fi: {ssid}")
            wifi.connect(ssid, password)
            for _ in range(15):
                if wifi.isconnected():
                    rssi = wifi.status('rssi')
                    print(f"Connected to {ssid}, RSSI:", rssi, "dBm")
                    print
                    return True
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Wi-Fi error: {e}")
        await asyncio.sleep(5)
    return False


        
def check_internet():
    try:
        addr = usocket.getaddrinfo("google.com", 80)[0][-1]
        s = usocket.socket()
        s.settimeout(2)  
        s.connect(addr)
        s.close()
        return True
    except Exception as e:
        print(f"Internet check failed: {e}")
        return False

