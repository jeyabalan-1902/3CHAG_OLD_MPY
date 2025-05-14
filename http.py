import esp32
import usocket as socket
import ujson
import time
import select
import utime
import machine
import uasyncio as asyncio
from machine import Timer
from nvs import nvs

async def handle_request(conn):
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

                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nCredentials Saved. Restarting...")
                conn.close()
                await asyncio.sleep(2)
                print("machine going to restart")
                machine.reset()
    except Exception as e:
        print("Error handling request:", e)
        try:
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid Request")
            conn.close()
        except:
            pass

async def start_http_server():
    addr = ("0.0.0.0", 8182)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    s.setblocking(False)

    print("HTTP Server started on 192.168.4.1:8182")

    while True:
        r, _, _ = select.select([s], [], [], 1.0) 
        if s in r:
            try:
                conn, addr = s.accept()
                print(f"Connection established with {addr}")
                await handle_request(conn)
            except Exception as e:
                print("Accept error:", e)
        await asyncio.sleep(0.1)