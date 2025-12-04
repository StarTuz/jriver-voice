import requests
import urllib.parse
import xml.etree.ElementTree as ET

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def send(path, params):
    url = f"{BASE_URL}{path}?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&{params}"
    print(f"Request: {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error Response: {r.text}")
        return r.text
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_smartlist_cleanup():
    print("\n--- Listing Playlists ---")
    # List playlists to find "VoiceCommandPlayback" or "TestSimple"
    resp = send("Playlists/List", "Action=XML")
    if resp:
        try:
            root = ET.fromstring(resp)
            # <Item>
            #  <Field Name="ID">123</Field>
            #  <Field Name="Name">VoiceCommandPlayback</Field>
            # </Item>
            
            for item in root.findall('Item'):
                pid = None
                name = None
                for field in item.findall('Field'):
                    if field.get('Name') == 'ID':
                        pid = field.text
                    elif field.get('Name') == 'Name':
                        name = field.text
                
                if name in ["VoiceCommandPlayback", "TestSimple", "TestSmartlist"]:
                    print(f"Found playlist '{name}' (ID: {pid}). Deleting...")
                    send("Playlists/Delete", f"Playlist={pid}")
                    
        except Exception as e:
            print(f"XML Error: {e}")

    print("\n--- Creating New Smartlist ---")
    # Try creating a very simple one
    # Name: VC_Test
    # Search: [Artist]=[Abba]
    
    search = urllib.parse.quote("[Artist]=[Abba]")
    params = f"Type=Smartlist&Name=VC_Test&Search={search}&CreateMode=1"
    send("Playlists/Add", params)

if __name__ == "__main__":
    test_smartlist_cleanup()
