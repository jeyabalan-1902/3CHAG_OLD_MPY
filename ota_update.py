import urequests
import machine
import ujson
import socket
from nvs import product_id

VERSION_FILE = "local_version.json"

def check_server_connection(ip, port):
    try:
        print(f"Checking connection to {ip}:{port}...")
        s = socket.socket()
        s.settimeout(5)
        s.connect((ip, port))
        print(f"Connection to {ip}:{port} successful.")
        s.close()
        return True
    except Exception as e:
        print(f"Connection check failed: {e}")
        return False

def get_local_version():
    try:
        with open(VERSION_FILE) as f:
            version_data = ujson.loads(f.read())
            print("Local version loaded:", version_data)
            return version_data["version"]
    except Exception as e:
        print("Error reading local version:", e)
        return "0.0.0"

def save_local_version(version):
    try:
        with open(VERSION_FILE, "w") as f:
            data = {"version": version}
            f.write(ujson.dumps(data))
            print("Local version saved:", data)
    except Exception as e:
        print("Error saving local version:", e)

def download_and_replace(url, local_path):
    try:
        print(f"Downloading: {url}")
        response = urequests.get(url)
        print(f"HTTP GET {url} - Status: {response.status_code}")
        if response.status_code == 200:
            with open(local_path, "w") as f:
                f.write(response.text)
            print(f"Updated {local_path}")
            response.close()
            return True
        else:
            print(f"Failed {url}: HTTP {response.status_code}")
            response.close()
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def send_ack_to_server(status, pid, server_ip, version):
    try:
        ack_url = f"http://{server_ip}:8080/ack"
        data = ujson.dumps({
            "status": status,
            "pid": pid,
            "version": version
        })
        headers = {'Content-Type': 'application/json'}
        print(f"Sending ACK to {ack_url} with data: {data}")
        response = urequests.post(ack_url, data=data, headers=headers)
        print(f"ACK Response Code: {response.status_code}")
        print("ACK Response Text:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send ACK:", e)

def ota_update_with_result(server_ip):
    server_port = 8080
    server_url = f"http://{server_ip}:{server_port}/version.json"

    if not check_server_connection(server_ip, server_port):
        print("Server not reachable before OTA. Skipping update.")
        send_ack_to_server("update_failed", f"{product_id}", server_ip, get_local_version())
        return False

    try:
        print(f"Checking for updates at {server_url}")
        r = urequests.get(server_url)
        print(f"Version Check Response Code: {r.status_code}")
        remote_version = r.json()
        print("Received remote version:", remote_version)
        r.close()

        local_version = get_local_version()
        print("Local version:", local_version)

        if remote_version["version"] != local_version:
            print(f"Updating from {local_version} to {remote_version['version']}")

            all_ok = True
            for filename in remote_version["files"]:
                file_url = f"http://{server_ip}:{server_port}/{filename}"
                if not download_and_replace(file_url, filename):
                    all_ok = False
                    break

            if all_ok:
                save_local_version(remote_version["version"])
                print("Update successful.")
                send_ack_to_server("update_success", f"{product_id}", server_ip, remote_version["version"])
                return True
            else:
                print("Update failed during file download.")
                send_ack_to_server("update_failed", f"{product_id}", server_ip, remote_version.get("version", "unknown"))
                return False

        else:
            print("Already up to date. No update required.")
            return False

    except Exception as e:
        print("OTA check failed:", e)
        send_ack_to_server("update_failed", f"{product_id}", server_ip, get_local_version())
        return False




