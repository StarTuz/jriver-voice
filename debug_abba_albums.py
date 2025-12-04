import requests
import xml.etree.ElementTree as ET
import urllib.parse

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def test_abba_albums():
    artist_name = "ABBA"
    
    print(f"Testing album search for: {artist_name}\n")
    
    # Try different filter formats
    test_cases = [
        ("Current format", f"[Artist]=[{artist_name}]"),
        ("Without outer brackets", f"Artist={artist_name}"),
        ("Simple equals", f"[Artist]={artist_name}"),
    ]
    
    for test_name, filter_expr in test_cases:
        print(f"\n{test_name}: {filter_expr}")
        encoded_filter = urllib.parse.quote(filter_expr)
        url = f"{BASE_URL}Library/Values?Field=Album&Filter={encoded_filter}&Key={ACCESS_KEY}"
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                albums = [item.text for item in root.findall('Item') if item.text]
                print(f"Found {len(albums)} albums:")
                for album in albums[:10]:  # Show first 10
                    print(f"  - {album}")
            else:
                print(f"Error: {response.text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")
    
    # Also try without any filter to see all albums
    print(f"\n\nAll albums (no filter):")
    url = f"{BASE_URL}Library/Values?Field=Album&Key={ACCESS_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            all_albums = [item.text for item in root.findall('Item') if item.text]
            # Look for albums that might have ABBA
            abba_albums = [a for a in all_albums if 'abba' in a.lower()]
            print(f"Albums with 'abba' in name: {len(abba_albums)}")
            for album in abba_albums:
                print(f"  - {album}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_abba_albums()
