import requests
import xml.etree.ElementTree as ET
import urllib.parse
import difflib

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def debug_holst_albums():
    artist = "Gustav Holst"
    target_album = "the planets"
    
    print(f"Debugging album search for Artist: '{artist}', Target Album: '{target_album}'\n")
    
    # 1. Search for tracks by this artist/composer using Files/Search
    query = urllib.parse.quote(artist)
    url = f"{BASE_URL}Files/Search?Query={query}&Key={ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('Item')
            print(f"Found {len(items)} tracks matching '{artist}'")
            
            # Collect unique albums
            albums_set = set()
            for item in items:
                item_artist = None
                item_composer = None
                item_album = None
                
                for field in item.findall('Field'):
                    name = field.get('Name')
                    if name == 'Artist':
                        item_artist = field.text
                    elif name == 'Composer':
                        item_composer = field.text
                    elif name == 'Album':
                        item_album = field.text
                
                # Check if artist or composer matches
                is_match = False
                if item_artist and artist.lower() in item_artist.lower():
                    is_match = True
                if item_composer and artist.lower() in item_composer.lower():
                    is_match = True
                    
                if is_match and item_album:
                    albums_set.add(item_album)
            
            print(f"\nUnique albums found for {artist}:")
            for album in sorted(albums_set):
                print(f"  - '{album}'")
                # Test matching score
                score = difflib.SequenceMatcher(None, target_album.lower(), album.lower()).ratio()
                print(f"    Match score with '{target_album}': {score:.2f}")
                
                # Test substring match
                if target_album.lower() in album.lower():
                    print(f"    ✅ Substring match!")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_holst_albums()
