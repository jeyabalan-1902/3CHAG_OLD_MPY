import esp32
import network
import ujson
import usocket
import usocket as socket
import ntptime
import time
import ubinascii
import urandom
import machine
import utime
from collections import OrderedDict
from machine import Pin, disable_irq, enable_irq, Timer
from time import sleep_ms
import uasyncio as asyncio
import struct

from machine import Pin, Timer
from nvs import get_product_id, get_stored_wifi_credentials, product_key, clear_wifi_credentials
from wifi_con import connect_wifi, check_internet, wifi, ap, wifi_led_task, internet_status
from http import start_http_server
from mqtt import mqtt_listener, mqtt_keepalive, connect_mqtt, client, hardReset
from gpio import Rst, http_server_led, press_start_time, reset_timer, S_Led

MAX_FAST_RETRIES = 50
FAST_RETRY_INTERVAL = 10
SLOW_RETRY_INTERVAL = 300

product_id = get_product_id()
print(f"stored Product ID:{product_id}")

def reset_callback(timer):
    global press_start_time
    if Rst.value() == 0:
        print("Reset button held for 500ms! Clearing credentials and restarting.")
        hardReset()
        clear_wifi_credentials()
        time.sleep(5)
        machine.reset()
        
def Rst_irq_handler(pin):
    global press_start_time
    if pin.value() == 0:             
        press_start_time = time.ticks_ms()
        reset_timer.init(mode=Timer.ONE_SHOT, period=5000, callback=reset_callback)
        
def print_firmware_version():
    try:
        with open("local_version.json") as f:
            version = ujson.loads(f.read())["version"]
            print(f"Firmware Version: {version}")
    except:
        print("Firmware Version: Unknown")


async def wifi_reconnect():
    retry_count = 0
    while True:
        if not wifi.isconnected():
            print("Wi-Fi disconnected! Attempting reconnection...")
            S_Led.value(1)
            time.sleep(0.5)
            S_Led.value(0)
            time.sleep(0.5)
            stored_ssid, stored_password = get_stored_wifi_credentials()

            if stored_ssid and stored_password:
                while retry_count < MAX_FAST_RETRIES:
                    S_Led.value(1)
                    time.sleep(0.5)
                    S_Led.value(0)
                    time.sleep(0.5)
                    print(f"Reconnection attempt {retry_count + 1} of {MAX_FAST_RETRIES}...")
                    if connect_wifi(stored_ssid, stored_password):
                        print("Wi-Fi Reconnected!")
                        retry_count = 0  
                        break
                    retry_count += 1
                    await asyncio.sleep(FAST_RETRY_INTERVAL)

                if not wifi.isconnected():
                    print("Switching to slow reconnection attempts every 5 minutes.")
                    while not wifi.isconnected():
                        S_Led.value(1)
                        time.sleep(0.5)
                        S_Led.value(0)
                        time.sleep(0.5)
                        if connect_wifi(stored_ssid, stored_password):
                            print("Wi-Fi Reconnected!")
                            retry_count = 0 
                            break
                        print("Reconnection failed, retrying in 5 minutes...")
                        await asyncio.sleep(SLOW_RETRY_INTERVAL)
            else:
                http_server_led()
                print("No stored Wi-Fi credentials. Restarting HTTP server...")
                await start_http_server()
        else:
            if not check_internet():
                print("Wi-Fi connected but no internet access. Reconnecting Wi-Fi...")
                wifi.disconnect()  
                await asyncio.sleep(5)  
            else:
                print("Wi-Fi and internet are connected.")
                await asyncio.sleep(10) 

                
Rst.irq(trigger=Pin.IRQ_FALLING, handler=Rst_irq_handler)
        
async def main():
    stored_ssid, stored_password = get_stored_wifi_credentials()
    if stored_ssid and stored_password:
        ap.active(False)
        while True:
            if connect_wifi(stored_ssid, stored_password):  
                print("Wi-Fi Connected. Starting background tasks...on the updated version")
                print_firmware_version()
                connect_mqtt()
                t1 = asyncio.create_task(mqtt_listener())
                t2 = asyncio.create_task(mqtt_keepalive())
                t3 = asyncio.create_task(wifi_reconnect())       
                await asyncio.gather(t1, t2, t3)
                break 
                
            else:
                print("Wi-Fi connected but no internet access. Reconnecting Wi-Fi...")
                wifi.disconnect() 
                await asyncio.sleep(5)        
    else:
        print("No WiFi credentials found, starting HTTP server...")
        http_server_led()
        await start_http_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Critical error:", e)
        machine.reset()
