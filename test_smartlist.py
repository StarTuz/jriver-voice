import requests
import urllib.parse

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def test_smartlist_alternatives():
    print("--- Testing Smartlist Alternatives ---")
    album_name = "Holst: The Planets, Op. 32"
    
    # Attempt 1: Double encoding? No, usually bad.
    # Attempt 2: Escape the comma? [Album]=[Holst: The Planets\, Op. 32]
    # JRiver search rules say special chars might need escaping.
    
    escaped_album = album_name.replace(",", "\\,")
    search_criteria = f"[Album]=[{escaped_album}]"
    encoded_search = urllib.parse.quote(search_criteria)
    
    url = f"{BASE_URL}Playlists/Add?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Type=Smartlist&Name=TestSmartlistEscaped&Search={encoded_search}&CreateMode=1"
    
    print(f"Attempt 1 (Escaped Comma): {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Attempt 3: Use 'PlayDoctor' but with 'Radio=0'? 
    # PlayDoctor is for radio. 
    # What about 'Playback/PlayPlaylist' with 'Zone=-1'?
    
    # Attempt 4: Use 'Library/Values' to get the file keys, then 'Playlists/Add' with 'FileKeys'?
    # This is much safer than search strings!
    print("\n--- Attempt 2: FileKeys ---")
    
    # 1. Get FileKeys for the album
    encoded_album_val = urllib.parse.quote(album_name)
    # We need to find the files. Library/Files?
    # Library/Files is unsupported on this version? Let's check.
    # User said Library/Files was unsupported/failing in summary.
    
    # Wait, Library/Values returns values, not file keys.
    # If Library/Files is broken, we are stuck with Search.
    
    # Let's try to just play a simple album to verify Smartlist works AT ALL.
    simple_album = "Blue"
    search_simple = f"[Album]=[{simple_album}]"
    encoded_simple = urllib.parse.quote(search_simple)
    url_simple = f"{BASE_URL}Playlists/Add?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Type=Smartlist&Name=TestSimple&Search={encoded_simple}&CreateMode=1"
    print(f"\nAttempt 3 (Simple Name): {url_simple}")
    try:
        r = requests.get(url_simple)
        print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_smartlist_alternatives()
