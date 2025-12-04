import requests
import xml.etree.ElementTree as ET

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def get_album_keys():
    print("Testing Library/Values to get Album Keys...")
    
    # Try to get Album and AlbumKey (if possible)
    # Note: Library/Values usually returns just the value, but let's see if we can get more
    # We'll try fetching "Album" and see what the XML looks like
    url = f"{BASE_URL}Library/Values?Field=Album&Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print("Response received.")
        
        # Parse XML
        root = ET.fromstring(response.text)
        
        # Print first few items to see structure
        items = root.findall('Item')
        print(f"Found {len(items)} albums.")
        
        for i, item in enumerate(items[:5]):
            print(f"Item {i}: {item.text}")
            print(f"  Attributes: {item.attrib}")
            
    except Exception as e:
        print(f"Error: {e}")

def try_files_query():
    print("\nTesting Library/Files with query...")
    # Try to find files for a specific album to see if we can get keys that way
    # We'll try a known album "Symphony No. 6"
    query = "[Album]=[Symphony No. 6]"
    url = f"{BASE_URL}Library/Files?Query={query}&Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success! We can query files.")
            print(response.text[:500]) # Print start of XML
        else:
            print("Failed to query files.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_album_keys()
    try_files_query()
