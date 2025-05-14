import esp32
import usocket as socket
import ujson
import time
import utime
import machine
import uasyncio as asyncio
from machine import Timer
from nvs import nvs


#HTTP connection request
def handle_request(conn):
    """Handles incoming HTTP requests."""
    try:
        request = conn.recv(1024).decode()
        print("Received Request:\n", request)

        if "POST /" in request:
            json_data = request.split("\r\n\r\n")[-1] 
            credentials = ujson.loads(json_data)

            ssid = credentials.get("ssid")
            password = credentials.get("password")

            if ssid and password:
                nvs.set_blob("wifi_ssid", ssid.encode())
                nvs.set_blob("wifi_password", password.encode())
                nvs.commit()
                print(f"WiFi credentials stored: SSID={ssid}, Password={password}")

                conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nCredentials Saved. Restarting...")
                conn.close()
                time.sleep(2)  
                print("machine going to restart")
                machine.reset()  
    except Exception as e:
        print("Error handling request:", e)
        conn.send("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid Request")
        conn.close()

async def start_http_server():
    addr = ("0.0.0.0", 8182)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("HTTP Server started on 192.168.4.1:8182")

    while True:
        conn, addr = s.accept()
        print(f"Connection established with {addr}")
        handle_request(conn)