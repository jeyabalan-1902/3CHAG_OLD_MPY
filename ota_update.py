import urequests
import machine
import ujson
from nvs import product_id

VERSION_FILE = "local_version.json"

def get_local_version():
    try:
        with open(VERSION_FILE) as f:
            return ujson.loads(f.read())["version"]
    except:
        return "0.0.0"

def save_local_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(ujson.dumps({"version": version}))

def download_and_replace(url, local_path):
    try:
        print(f"Downloading: {url}")
        response = urequests.get(url)
        if response.status_code == 200:
            with open(local_path, "w") as f:
                f.write(response.text)
            print(f"Updated {local_path}")
            return True
        else:
            print(f"Failed {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def send_ack_to_server(status, pid):
    try:
        ack_url = "http://192.168.0.59:8080/ack"  
        data = ujson.dumps({
            "status": status,
            "pid": pid
        })
        headers = {'Content-Type': 'application/json'}
        response = urequests.post(ack_url, data=data, headers=headers)
        print("ACK sent:", response.status_code)
        response.close()
    except Exception as e:
        print("Failed to send ACK:", e)

def ota_update_with_result():
    server_url = "http://192.168.0.59:8080/version.json"  

    try:
        r = urequests.get(server_url)
        remote_version = r.json()
        r.close()

        local_version = get_local_version()
        if remote_version["version"] != local_version:
            print(f"Updating from {local_version} to {remote_version['version']}")

            all_ok = True
            for filename in remote_version["files"]:
                file_url = f"http://192.168.0.59:8080/{filename}"
                if not download_and_replace(file_url, filename):
                    all_ok = False
                    break

            if all_ok:
                save_local_version(remote_version["version"])
                print("Update successful.")
                send_ack_to_server("update_success", f"{product_id}")
                return True
            else:
                print("Update failed.")
                send_ack_to_server("update_failed", f"{product_id}")
                return False

        else:
            print("Already up to date. No update required.")
            return False

    except Exception as e:
        print("OTA check failed:", e)
        send_ack_to_server("update_failed", f"{product_id}")
        return False