import os
import subprocess
import time
import serial

# === CONFIGURATION ===
PORT = "COM4"  # Change to your ESP32's port
FIRMWARE = "ESP32_GENERIC-OTA-20250415-v1.25.0.bin"
PY_FILES = [
    "main.py", "mqtt.py", "wifi_con.py", "gpio.py",
    "http.py", "ota_update.py", "nvs.py", "local_version.json"
]

def wait_for_micropython_ready(port, timeout=10):
    print(f"⏳ Waiting for MicroPython REPL on {port}...", end="", flush=True)
    try:
        with serial.Serial(port, 115200, timeout=0.5) as ser:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    if b"MicroPython" in data or b">>>" in data:
                        print(" ✅ Ready.")
                        return True
                print(".", end="", flush=True)
                time.sleep(0.5)
    except Exception as e:
        print(f"\n⚠️ Serial error: {e}")
    print("\n❌ MicroPython did not start in time.")
    return False

# === STEP 0: Prompt for Product ID ===
product_id = input("🔐 Enter Product ID to flash into NVS: ").strip()

# === STEP 1: Erase Flash ===
print("🧹 Erasing flash...")
subprocess.run(["python", "-m", "esptool", "--chip", "esp32", "--port", PORT, "erase_flash"])

# === STEP 2: Flash Firmware ===
print("📦 Flashing MicroPython firmware...")
subprocess.run([
    "python", "-m", "esptool", "--chip", "esp32", "--port", PORT,
    "--baud", "460800", "write_flash", "-z", "0x1000", FIRMWARE
])

# === STEP 3: Wait for ESP32 to fully boot MicroPython ===
if not wait_for_micropython_ready(PORT):
    print("❌ Aborting upload due to MicroPython not responding.")
    exit(1)

# === STEP 4: Upload project files ===
print("📤 Uploading Python files to ESP32...")
for file in PY_FILES:
    print(f"➡ Uploading {file}...")
    result = subprocess.run(
        ["mpremote", "connect", PORT, "fs", "cp", file, ":"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to upload {file}:\n{result.stderr}")
    else:
        print(f"✅ Uploaded {file}")

# === STEP 5: Write Product ID to NVS ===
print("💾 Writing Product ID into ESP32 NVS...")

nvs_code = f"""
import esp32
nvs = esp32.NVS("storage")
nvs.set_blob("product_id", b"{product_id}")
nvs.commit()
print("Product ID set to: {product_id}")
"""

subprocess.run(["mpremote", "connect", PORT, "exec", nvs_code])

# === STEP 6: Run main.py ===
print("🏃 Running main.py...")
subprocess.run(["mpremote", "connect", PORT, "run", "main.py"])

print("\n✅ DONE: Firmware flashed, Product ID stored, and main.py running.")