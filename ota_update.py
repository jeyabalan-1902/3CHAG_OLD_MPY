import urequests
import machine
import ujson

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

def ota_update():
    server_url = "http://192.168.x.x:8080/version.json"  

    try:
        r = urequests.get(server_url)
        remote_version = r.json()
        r.close()

        local_version = get_local_version()
        if remote_version["version"] != local_version:
            print(f"Updating from {local_version} to {remote_version['version']}")

            all_ok = True
            for filename in remote_version["files"]:
                file_url = f"http://192.168.x.x:8080/{filename}"
                if not download_and_replace(file_url, filename):
                    all_ok = False
                    break

            if all_ok:
                save_local_version(remote_version["version"])
                print("Update successful! Restarting...")
                machine.reset()
            else:
                print("Update failed. Not restarting.")

        else:
            print("Already up to date.")

    except Exception as e:
        print("OTA check failed:", e)
