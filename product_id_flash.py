import esp32
import machine

nvs = esp32.NVS("storage")
product_key = "product_id"



def get_product_id():
    try:
        buf = bytearray(32)  
        length = nvs.get_blob(product_key, buf)  
        return buf[:length].decode() 
    except OSError:
        return None 

# Function to save Product ID
def set_product_id(product_id):
    encoded_id = product_id.encode()  
    nvs.set_blob(product_key, encoded_id)  
    nvs.commit()  
    print("Product ID saved in NVS.")

# Function to delete Product ID
def delete_product_id():
    try:
        nvs.erase_key(product_key)
        nvs.commit()
        print("Product ID deleted from NVS.")
    except OSError:
        print("No stored Product ID to delete.")

def timed_input(prompt, timeout):
    print(f"{prompt} (Waiting {timeout} seconds)... ", end="", flush=True)
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)  # Use positional args
    if rlist:
        return sys.stdin.readline().strip()
    print("\nNo response. Continuing...")
    return None  # Return None if timeout occurs

# Check if Product ID exists
product_id = get_product_id()

if product_id:
    print(f"Stored Product ID: {product_id}")
    delete_option = input("Do you want to delete the stored Product ID? (yes/no): ").strip().lower()
    
    if delete_option == "yes":
        delete_product_id()
        product_id = None  # Reset product_id so new one is requested
#     print(f"\nStored Product ID: {product_id}")
#     delete_option = timed_input("Do you want to delete the stored Product ID? (yes/no)", timeout=5).strip().lower()
#     
#     if delete_option and delete_option.lower() == "yes":
#         delete_product_id()
#         product_id = None  # Reset product_id so new one is requested



# If no Product ID is stored, ask for a new one
if product_id is None:
    product_id = input("Enter Product ID: ").strip()
    if product_id:
        set_product_id(product_id)

# Continue with your main logic using the stored product_id
print(f"Using Product ID: {product_id}")
