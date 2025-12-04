import requests
import urllib.parse

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
        if r.status_code != 200:
            print(f"Error Response: {r.text}")
        return r.text
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_playback_methods():
    print("\n--- Testing PlayDoctor with Radio=0 ---")
    # PlayDoctor usually shuffles. Can we turn off radio mode?
    # Some docs suggest 'Radio=0' or 'Shuffle=0'?
    # Or maybe just Playback/Play with a search?
    
    album = "Vaughan Williams: Symphonies Nos. 4 & 6"
    encoded_album = urllib.parse.quote(album)
    
    # Method 1: PlayDoctor with Radio=0 (Guess)
    params = f"Seed={encoded_album}&Radio=0"
    send("Playback/PlayDoctor", params)
    
    print("\n--- Testing Playback/Play with Search ---")
    # Does Playback/Play accept a search?
    # Usually it takes a Key, or Playlist.
    # But maybe 'File' param can be a search string?
    # Or 'Location'?
    
    # Let's try to set the playlist to the search results?
    # "Playback/SetPlaylist"? No.
    
    # What about "Playback/Play" with "Argument" being the search?
    # This is how command line works: mc30.exe /Play [Search]
    # MCWS equivalent?
    
    # Maybe "Playback/Play" isn't the right command.
    # Is there "Library/Search"? No, unsupported.
    
    # Let's try "Playback/Play" with "Filename" as the search?
    # Probably not.
    
    pass

if __name__ == "__main__":
    test_playback_methods()
