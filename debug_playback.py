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

def test_library_files():
    print("\n--- Testing Library/Files ---")
    # Try to get files for a specific album
    album = "Vaughan Williams: Symphonies Nos. 4 & 6"
    encoded_album = urllib.parse.quote(album)
    
    # We want Key and Track #
    params = f"Action=JSON&Filter=[Album]=[{encoded_album}]&Fields=Key,Track #"
    
    # Note: Action=JSON might not be supported on old versions, let's try XML default first if JSON fails?
    # The user script uses XML parsing, so let's stick to XML for safety unless JSON is preferred.
    # But wait, the user said "Library/Files" was unsupported/failing.
    # Let's try default (XML) first.
    
    params = f"Filter=[Album]=[{encoded_album}]&Fields=Key,Track #"
    response = send("Library/Files", params)
    
    if response:
        print("Success! Parsing keys...")
        try:
            root = ET.fromstring(response)
            # XML structure for Library/Files:
            # <Response Status="OK">
            # <Item>
            #  <Field Name="Key">123</Field>
            #  <Field Name="Track #">1</Field>
            # </Item>
            # ...
            
            files = []
            for item in root.findall('Item'):
                key = None
                track = 0
                for field in item.findall('Field'):
                    if field.get('Name') == 'Key':
                        key = field.text
                    elif field.get('Name') == 'Track #':
                        track = int(field.text) if field.text else 0
                if key:
                    files.append((track, key))
            
            # Sort by track
            files.sort(key=lambda x: x[0])
            print(f"Found {len(files)} files. First 5: {files[:5]}")
            return [f[1] for f in files]
            
        except Exception as e:
            print(f"XML Parse Error: {e}")
            print(f"Raw: {response[:200]}")
    return None

def test_smartlist_simple():
    print("\n--- Testing Smartlist (Simple) ---")
    # Simple album name
    album = "Blue"
    encoded_album = urllib.parse.quote(album)
    search = urllib.parse.quote(f"[Album]=[{album}]")
    
    params = f"Type=Smartlist&Name=TestSimple&Search={search}&CreateMode=1"
    send("Playlists/Add", params)

if __name__ == "__main__":
    keys = test_library_files()
    if keys:
        print("\n--- Testing Playlist Creation via FileKeys ---")
        # If we got keys, try to create a playlist with them
        keys_str = ",".join(keys)
        # Playlists/Add with FileKeys
        # Param: FileKeys (comma separated)
        # We also need a Playlist ID or Path? 
        # "Playlists/Add" creates a playlist.
        # Params: Name, Type=Path? No, Type=Static?
        # If we just want to play them, maybe "Playback/PlayPlaylist" isn't needed if we can "Playback/Play" with keys?
        # "Playback/Play" doesn't take keys directly usually.
        # "Playlists/Add" creates it.
        
        # Let's try creating a standard playlist (not smartlist) with these keys.
        # Type defaults to standard if not specified?
        params = f"Name=VoiceCmd&Type=Standard&FileKeys={keys_str}&CreateMode=1"
        send("Playlists/Add", params)
        
        # Then play it
        print("Playing it...")
        send("Playback/PlayPlaylist", "Playlist=VoiceCmd&PlaylistType=Path")

    test_smartlist_simple()
