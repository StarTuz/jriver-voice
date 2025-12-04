import requests
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def list_artists():
    print("--- Listing First 50 Artists ---")
    # Get all artists, limit to 50
    url = f"{BASE_URL}Library/Values?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Field=Artist&Limit=50"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.text)
        artists = [item.text for item in root.findall('Item')]
        for a in artists:
            print(a)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_artists()
