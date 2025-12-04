import requests
import xml.etree.ElementTree as ET

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def check_artists():
    print("Checking for Abba in library...\n")
    url = f"{BASE_URL}Library/Values?Field=Artist&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            artists = [item.text for item in root.findall('Item') if item.text]
            
            # Look for matches to "abba"
            matches = [a for a in artists if 'abba' in a.lower()]
            
            if matches:
                print(f"Found {len(matches)} artist(s) with 'abba':")
                for artist in matches:
                    print(f"  - {artist}")
            else:
                print("No artists found with 'abba' in the name")
                
                # Also check for similar
                print("\nArtists starting with 'A' or 'C':")
                similar = [a for a in artists if a.lower().startswith('a') or a.lower().startswith('c')][:20]
                for artist in similar:
                    print(f"  - {artist}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_artists()
