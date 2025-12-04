import requests
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def list_albums():
    print("--- Listing First 100 Albums ---")
    url = f"{BASE_URL}Library/Values?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Field=Album&Limit=100"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.text)
        albums = [item.text for item in root.findall('Item')]
        for a in albums:
            print(a)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_albums()
