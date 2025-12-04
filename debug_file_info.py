import requests
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def check_file_info(file_key):
    print(f"--- Checking File/GetInfo for Key {file_key} ---")
    url = f"{BASE_URL}File/GetInfo?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&File={file_key}"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.text)
        # <Item Name="Track #">5</Item>
        for item in root.findall('Item'):
            name = item.get('Name')
            val = item.text
            if name in ['Track #', 'Total Tracks', 'Name', 'Album']:
                print(f"{name}: {val}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Use the key from previous log: 3694
    check_file_info(3694)
