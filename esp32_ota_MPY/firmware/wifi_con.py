import esp32
import machine
import urandom
import network
import usocket
import usocket as socket
import time
import utime
import ubinascii
from nvs import get_stored_wifi_credentials
from time import sleep_ms
from machine import Timer
from nvs import get_product_id, product_key
from mqtt import product_id
from gpio import S_Led

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=f"onwords-{product_id}", authmode=network.AUTH_OPEN)

while ap.active() is False:
    time.sleep(1)
print("AP Mode Active. IP Address:", ap.ifconfig()[0])

def connect_wifi(ssid, password):
    while True:
        try:
            print(f"Attempting to connect to Wi-Fi: {ssid}")
            wifi.connect(ssid, password)

            for _ in range(15): 
                if wifi.isconnected():
                    print("Connected to WiFi:", ssid)
                    print("IP Address:", wifi.ifconfig()[0])
                    return True
                
                else:
                    S_Led.value(1)
                    time.sleep(0.5)
                    S_Led.value(0)
                    time.sleep(0.5)
                    S_Led.value(1)
                    time.sleep(0.5)
                    S_Led.value(0)
                    time.sleep(0.5)
                    
                time.sleep(2) 

            print("WiFi connection failed! Retrying...")
        except OSError as e:
            print(f"WiFi connection error: {e}. Retrying...")
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying...")
        time.sleep(5)

        
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
