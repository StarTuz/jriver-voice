import requests
import xml.etree.ElementTree as ET
import urllib.parse

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def debug_planets_metadata():
    query = "The Planets"
    print(f"Searching for tracks matching: '{query}'\n")
    
    encoded_query = urllib.parse.quote(query)
    url = f"{BASE_URL}Files/Search?Query={encoded_query}&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('Item')
            print(f"Found {len(items)} tracks\n")
            
            for i, item in enumerate(items[:5]):  # Show first 5
                print(f"Track {i+1}:")
                for field in item.findall('Field'):
                    name = field.get('Name')
                    if name in ['Name', 'Artist', 'Composer', 'Album', 'Album Artist']:
                        print(f"  {name}: {field.text}")
                print()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_planets_metadata()
