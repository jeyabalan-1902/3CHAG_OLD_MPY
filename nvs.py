import esp32

nvs = esp32.NVS("storage")
product_key = "product_id"
        
def store_pid(product_id):
    encoded_id = product_id.encode()  
    nvs.set_blob(product_key, encoded_id)  
    nvs.commit()  
    print("Product ID saved in NVS.")

def get_product_id():
    try:
        buf = bytearray(32)
        length = nvs.get_blob(product_key, buf)
        return buf[:length].decode()
    except OSError:
        return None
    
product_id = get_product_id()
print(product_id)

def get_stored_wifi_credentials():
    try:
        ssid_buf = bytearray(38)
        pass_buf = bytearray(38)
        if nvs.get_blob("wifi_ssid", ssid_buf) and nvs.get_blob("wifi_password", pass_buf):
            stored_ssid = ssid_buf.decode().strip("\x00")
            stored_password = pass_buf.decode().strip("\x00")
            return stored_ssid, stored_password
    except:
        pass
    return None, None

def clear_wifi_credentials():
    try:
        nvs.erase_key("wifi_ssid")
        nvs.erase_key("wifi_password")
        nvs.commit()
    except OSError as e:
        print("Error clearing NVS:", e)