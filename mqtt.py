import esp32
from umqtt.simple import MQTTClient
import ujson
import ntptime
import time
import ubinascii
import urandom
import machine
import utime
from collections import OrderedDict
from machine import Timer, Pin
import uasyncio as asyncio
from nvs import get_product_id, product_key, clear_wifi_credentials, store_pid
from gpio import R1,R2,R3,S_Led


client = None
product_id = get_product_id()
mqtt_client = 0

BROKER_ADDRESS = "mqtt.onwords.in"
MQTT_CLIENT_ID = product_id
TOPIC_STATUS = f"onwords/{product_id}/status"
TOPIC_GET_CURRENT_STATUS = f"onwords/{product_id}/getCurrentStatus"
TOPIC_SOFTRST = f"onwords/{product_id}/softReset"
TOPIC_CURRENT_STATUS = f"onwords/{product_id}/currentStatus"
TOPIC_PID = f"onwords/{product_id}/storePid"
TOPIC_FIRMWARE = f"onwords/{product_id}/firmware"
PORT = 1883
USERNAME = "Nikhil"
MQTT_PASSWORD = "Nikhil8182"
MQTT_KEEPALIVE = 60


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

#MQTT callback
def mqtt_callback(topic, msg):
    topic_str = topic.decode()
    print(f"Received from {topic_str}: {msg.decode()}")

    if topic_str == f"onwords/{product_id}/status":
        try:
            data = ujson.loads(msg)

            if "action" in data and data["action"] == "doubleGate":
                print("received payload: {}".format(data))
                R2.value(1)
                R3.value(1)
                time.sleep_ms(600)
                R2.value(0)
                R3.value(0)
                status_msg = ujson.dumps({"action": "doubleGate"})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)
            
            if "action" in data and data["action"] == "singleGate":
                print("received payload: {}".format(data))
                R1.value(1)  
                time.sleep_ms(600)
                R1.value(0)  
                status_msg = ujson.dumps({"action": "singleGate"})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)

        except ValueError as e:
            print("Error parsing JSON:", e)

    if topic_str == f"onwords/{product_id}/getCurrentStatus":
        try:
            data = ujson.loads(msg)
            print("received payload: {}".format(data))
            if "request" in data and data["request"] == "getCurrentStatus":
                status_msg = ujson.dumps({"action": ""})
                client.publish(TOPIC_CURRENT_STATUS, status_msg)

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