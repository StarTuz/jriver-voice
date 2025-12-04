import requests
import urllib.parse
import difflib

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def test_smartlist_encoding():
    print("--- Testing Smartlist Encoding ---")
    # The album that caused 500 error before
    album_name = "Holst: The Planets, Op. 32"
    
    # Proper encoding
    encoded_album = urllib.parse.quote(album_name)
    # Note: The search criteria itself needs to be safe. 
    # [Album]=[Holst: The Planets, Op. 32] -> The whole string needs to be safe for the URL.
    # The API expects: Search=[Album]=[Val]
    # So we construct the unencoded search string first, then encode it?
    # Or does JRiver expect the value inside [] to be raw?
    # Let's try encoding the VALUE inside the brackets.
    
    # Actually, requests.get(params=...) handles this automatically. 
    # But the script builds the URL manually.
    # Let's emulate the manual build with quote.
    
    search_criteria = f"[Album]=[{album_name}]"
    encoded_search = urllib.parse.quote(search_criteria)
    
    url = f"{BASE_URL}Playlists/Add?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Type=Smartlist&Name=TestSmartlist&Search={encoded_search}&CreateMode=1"
    
    print(f"URL: {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_fuzzy_improvements():
    print("\n--- Testing Fuzzy Improvements ---")
    query = "vaughan williams simply number six album"
    target = "Vaughan Williams: Symphony No. 6 / The Lark Ascending"
    
    # 1. Normalize
    normalized = query.lower().replace("number", "no.").replace("simply", "symphony")
    print(f"Normalized: {normalized}")
    
    # 2. Match
    s = difflib.SequenceMatcher(None, normalized, target.lower()).ratio()
    print(f"Score against target: {s:.2f}")

if __name__ == "__main__":
    test_smartlist_encoding()
    test_fuzzy_improvements()
