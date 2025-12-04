import requests
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def check_info():
    print("--- Checking Playback/Info Fields ---")
    url = f"{BASE_URL}Playback/Info?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.text)
        for item in root.findall('Item'):
            name = item.get('Name')
            val = item.text
            print(f"{name}: {val}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_info()
