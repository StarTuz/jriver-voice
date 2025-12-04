import requests
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def get_current_key():
    url = f"{BASE_URL}Playback/Info?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.text)
        for item in root.findall('Item'):
            if item.get('Name') == 'FileKey':
                return item.text
    except:
        pass
    return None

def check_file_info():
    key = get_current_key()
    if not key:
        print("No FileKey found (nothing playing?)")
        return

    print(f"--- Checking File/GetInfo for Key {key} ---")
    url = f"{BASE_URL}File/GetInfo?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&File={key}"
    try:
        r = requests.get(url)
        print(f"Raw Response: {r.text[:500]}...") # Print first 500 chars
        
        root = ET.fromstring(r.text)
        # Dump all fields
        for item in root.findall('Field'):
            print(f"{item.get('Name')}: {item.text}")
            
        # Also check for 'Item' tags? 
        # File/GetInfo usually returns <MPL> <Item> <Field>...</Field> </Item> </MPL>
        # Or just <Response> <Item>...</Item> </Response>?
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_file_info()
