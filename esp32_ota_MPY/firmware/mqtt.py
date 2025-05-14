import esp32
from umqtt.simple import MQTTClient
import ujson
import ntptime
import time
import ubinascii
import urandom
import machine
import utime
import network
from collections import OrderedDict
from machine import Timer, Pin
import uasyncio as asyncio
from nvs import get_product_id, product_key, clear_wifi_credentials
from gpio import R1,R2,R3, S_Led


client = None
product_id = get_product_id()

BROKER_ADDRESS = "mqtt.onwords.in"
MQTT_CLIENT_ID = product_id
TOPIC_STATUS = f"onwords/{product_id}/status"
TOPIC_GET_CURRENT_STATUS = f"onwords/{product_id}/getCurrentStatus"
TOPIC_SOFTRST = f"onwords/{product_id}/softReset"
TOPIC_CURRENT_STATUS = f"onwords/{product_id}/currentStatus"
TOPIC_PID = f"onwords/{product_id}/storePid"
TOPIC_FIRMWARE = f"onwords/{product_id}/firmware"
TOPIC_DEVICE_LOG = f"onwords/{product_id}/switch"
PORT = 1883
USERNAME = "Nikhil"
MQTT_PASSWORD = "Nikhil8182"
MQTT_KEEPALIVE = 60

def get_timestamp():
    try:
        ntptime.settime()  
        return utime.time() * 1000  
    except:
        return 0 

def hardReset():
    global client
    if client is None:
        print("MQTT client not initialized. Cannot publish hard reset message.")
    else:
        try:
            payload = {"id": product_id}
            client.publish("onwords/hardReset", ujson.dumps(payload))
            print("Hard reset published to MQTT broker.")
        except Exception as e:
            print(f"Failed to publish hard reset message: {e}")

#publish devices state
def publish_state():
    global client
    if client:
        state = {
            "device1": R1.value(),
            "device2": R2.value(),
            "device3": R3.value()
        }

        client.publish(TOPIC_CURRENT_STATUS, ujson.dumps(state))
        print("Published state:", state)
    else:
        print("MQTT client not connected!")
 
 
#publish Device log
def publish_deviceLog(device, state):
    global client
    if client:
        log = {
            device: state,
            "id": product_id,
            "client_id": "Switch",
            "ip": network.WLAN(network.STA_IF).ifconfig()[0],
            "time_stamp": get_timestamp()
        }
        client.publish(TOPIC_DEVICE_LOG, ujson.dumps(log))
        print("log published:", log)       
    else:
        print("mqtt client not connected")

#MQTT callback
def mqtt_callback(topic, msg):
    topic_str = topic.decode()
    print(f"Received from {topic_str}: {msg.decode()}")

    if topic_str == f"onwords/{product_id}/status":
        try:
            data = ujson.loads(msg)

            if "device1" in data and data["device1"] in [0, 1]:
                R1.value(data["device1"])
                status_msg = ujson.dumps({"device1": data["device1"]})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)

            if "device2" in data and data["device2"] in [0, 1]:
                R2.value(data["device2"])
                status_msg = ujson.dumps({"device2": data["device2"]})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)

            if "device3" in data and data["device3"] in [0, 1]:
                R3.value(data["device3"])
                status_msg = ujson.dumps({"device3": data["device3"]})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)

        except ValueError as e:
            print("Error parsing JSON:", e)

    if topic_str == f"onwords/{product_id}/getCurrentStatus":
        try:
            publish_state()

        except ValueError as e:
            print("Error parsing JSON:", e)

    if topic_str == f"onwords/{product_id}/softReset":
        try:
            clear_wifi_credentials()
            state = {
                "status": True
            }
            client.publish(TOPIC_SOFTRST, ujson.dumps(state))
            time.sleep(5)
            machine.reset()

        except ValueError as e:
            print("Error:", e)
            
    if topic_str == f"onwords/{product_id}/storePid":
        try:
            data = ujson.loads(msg)
            if "pid" in data:
                store_pid(data["pid"])
                status_msg = ujson.dumps({"pid": data["pid"]})
                client.publish(TOPIC_PID, status_msg)
                print("restarting device now....")
                time.sleep(2)
                machine.reset()
                
        except Exception as e:
            print("Error in JSON or storing:", e)
            
    
    if topic_str == f"onwords/{product_id}/firmware":
        try:
            data = ujson.loads(msg)
            if data.get("update") is True:
                print("OTA update trigger received via MQTT!")

                # Notify the server that OTA started
                status_msg = ujson.dumps({"status": "update_started", "pid": product_id})
                client.publish(f"onwords/{product_id}/firmware", status_msg)

                import ota_update
                success = ota_update.ota_update_with_result()

                # Notify server about result
                if success:
                    status_msg = ujson.dumps({"status": "update_success", "pid": product_id})
                else:
                    status_msg = ujson.dumps({"status": "update_failed", "pid": product_id})

                client.publish(f"onwords/{product_id}/firmware", status_msg)
                time.sleep(3)

                # Restart if successful
                if success:
                    print("OTA complete, rebooting now...")
                    machine.reset()

        except Exception as e:
            print("Failed to parse OTA command:", e)

#Connect MQTT
def connect_mqtt():
    global client
    global mqtt_connect
    try:
        client = MQTTClient(client_id=product_id, server=BROKER_ADDRESS, port=PORT, user=USERNAME, password=MQTT_PASSWORD, keepalive=MQTT_KEEPALIVE)
        client.set_callback(mqtt_callback)
        client.connect()
        S_Led.value(1)
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_GET_CURRENT_STATUS)
        client.subscribe(TOPIC_SOFTRST)
        client.subscribe(TOPIC_PID)
        client.subscribe(TOPIC_FIRMWARE)
        print(f"Subscribed to {TOPIC_STATUS}")
        print(f"Subscribed to {TOPIC_GET_CURRENT_STATUS}")
        print(f"Subscribed to {TOPIC_SOFTRST}")
        print(f"Subscribed to {TOPIC_PID}")
        print(f"Subscribed to {TOPIC_FIRMWARE}")
        mqtt_client = 1 
        return client
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        mqtt_client = 0
        return None

#Reconnect MQTT
def reconnect_mqtt():
    global client
    print("Reconnecting MQTT...")
    try:
        if client:
            client.disconnect()
    except:
        pass
    client = None
    await asyncio.sleep(2)  
    return connect_mqtt()

#MQTT Listen
async def mqtt_listener():
    while True:
        try:
            if client:
                client.check_msg()
        except Exception as e:
            print("Error checking MQTT:", e)
            await reconnect_mqtt()
        await asyncio.sleep(0.1)

#keep alive
async def mqtt_keepalive():
    while True:
        try:
            if client:
                print("Sending MQTT PINGREQ")
                client.ping() 
        except Exception as e:
            print("MQTT Keep-Alive failed:", e)
            await reconnect_mqtt()
        await asyncio.sleep(MQTT_KEEPALIVE // 2)
        
        
def process_F1():
    new_state = not R1.value()
    R1.value(new_state)
    print("switch 1 toggled")
    publish_state()
    publish_deviceLog("device1", new_state)
    
def process_F2():
    new_state = not R2.value()
    R2.value(new_state)
    print("Switch 2 toggled")
    publish_state()
    publish_deviceLog("device2", new_state)
    

def process_F3():
    new_state = not R3.value()
    R3.value(new_state)
    print("Switch 3 toggled")
    publish_state()
    publish_deviceLog("device3", new_state)