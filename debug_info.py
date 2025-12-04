import requests
import urllib.parse
import xml.etree.ElementTree as ET
import time

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def send(path, params=""):
    url = f"{BASE_URL}{path}?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&{params}"
    print(f"Request: {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        return r.text
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_whats_playing():
    print("\n--- Testing Playback/Info ---")
    resp = send("Playback/Info", "Zone=-1")
    if resp:
        try:
            root = ET.fromstring(resp)
            # <Response ...>
            #  <Item Name="Name">Track Name</Item>
            #  <Item Name="Artist">Artist Name</Item>
            #  ...
            
            info = {}
            for item in root.findall('Item'):
                name = item.get('Name')
                val = item.text
                if name in ['Name', 'Artist', 'Album', 'Status']:
                    info[name] = val
            
            print(f"Current Info: {info}")
        except Exception as e:
            print(f"XML Error: {e}")

def test_playdoctor_search():
    print("\n--- Testing PlayDoctor with Search String ---")
    # Try seeding with the specific work name
    query = "Vaughan Williams Symphony No. 6"
    encoded_query = urllib.parse.quote(query)
    
    # Does Seed accept a raw string?
    params = f"Seed={encoded_query}&Radio=0"
    send("Playback/PlayDoctor", params)
    
    # Wait a bit and check what's playing
    time.sleep(2)
    test_whats_playing()

if __name__ == "__main__":
    test_whats_playing()
    # Uncomment to test playback change (might interrupt user)
    # test_playdoctor_search()
