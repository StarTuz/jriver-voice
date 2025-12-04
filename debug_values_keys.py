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
        if r.status_code == 200:
            return r.text
        else:
            print(f"Error Response: {r.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_values_keys():
    print("\n--- Testing Library/Values for Keys ---")
    # Can we get keys for an album using Library/Values?
    # Field=Key?
    album = "Vaughan Williams: Symphonies Nos. 4 & 6"
    encoded_album = urllib.parse.quote(album)
    
    params = f"Field=Key&Filter=[Album]=[{encoded_album}]"
    response = send("Library/Values", params)
    
    if response:
        print("Response received.")
        try:
            root = ET.fromstring(response)
            keys = [item.text for item in root.findall('Item')]
            print(f"Found {len(keys)} keys: {keys[:5]}")
            
            # If we have keys, we need to know the track order!
            # Library/Values just returns a list of values, probably sorted by the value itself (Key).
            # This won't help with order.
            
            # We need to get keys AND Track #.
            # Library/Values only returns one field.
            
            # Maybe we can get "Track # - Key" as a calculated field?
            # Field=[Track #] - [Key] ?
            # JRiver allows expression fields.
            
            # Let's try requesting a calculated field.
            # Note: Field param usually takes a database field.
            # But maybe we can pass an expression?
            
        except Exception as e:
            print(f"Error: {e}")

def test_expression_field():
    print("\n--- Testing Expression Field ---")
    album = "Vaughan Williams: Symphonies Nos. 4 & 6"
    encoded_album = urllib.parse.quote(album)
    
    # Expression: [Track #]_[Key]
    # We need to pad Track # to sort correctly. PadNumber([Track #], 2)
    
    # URL Encode the expression?
    # Field=Expression
    # Value=... ? No, Library/Values takes 'Field'.
    
    # If we can't use Library/Files, getting ordered keys is hard.
    
    # ALTERNATIVE:
    # Use `Playlists/Add` with `Type=Standard` and `Search`?
    # Does `Type=Standard` support `Search`? Probably not.
    
    # Let's try `Playlists/Add` with `Type=Smartlist` but DIFFERENT SYNTAX.
    # Maybe the 500 is because the playlist name already exists?
    # "VoiceCommandPlayback"
    # Try deleting it first?
    
    print("\n--- Deleting Playlist First ---")
    # Playlists/Delete?
    # We need the Playlist ID.
    # Playlists/List to find it.
    
    list_resp = send("Playlists/List", "Action=JSON") # Try JSON
    if not list_resp:
        list_resp = send("Playlists/List", "") # XML
        
    # If we can find "VoiceCommandPlayback", delete it.
    
    # Then try creating Smartlist again.
    
    # Also, try `Playlists/Add` with `Type=Path`? No.
    
    pass

if __name__ == "__main__":
    test_values_keys()
