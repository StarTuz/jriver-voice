import requests
import xml.etree.ElementTree as ET

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def find_abba_tracks():
    print("Finding tracks by ABBA using Files/Search...\n")
    
    # Use Files/Search to find any file with ABBA
    import urllib.parse
    query = urllib.parse.quote("ABBA")
    url = f"{BASE_URL}Files/Search?Query={query}&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('Item')
            print(f"Found {len(items)} files matching 'ABBA'\n")
            
            if items:
                # Look at first item's fields to see what fields exist
                first_item = items[0]
                print("Fields in first ABBA track:")
                for field in first_item.findall('Field'):
                    field_name = field.get('Name')
                    field_value = field.text
                    if field_name in ['Name', 'Artist', 'Album Artist', 'Album', 'Composer']:
                        print(f"  {field_name}: {field_value}")
                
                # Check if there's an Album Artist field
                print("\n\nChecking all tracks for Album Artist field...")
                albums_set = set()
                for item in items[:20]:  # Check first 20
                    for field in item.findall('Field'):
                        if field.get('Name') == 'Album':
                            albums_set.add(field.text)
                
                print(f"\nUnique albums in ABBA tracks:")
                for album in sorted(albums_set):
                    print(f"  - {album}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_abba_tracks()
