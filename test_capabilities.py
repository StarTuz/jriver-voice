import requests

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def send_command(path, params=""):
    # Added Response=json to force JSON output
    url = f"{BASE_URL}{path}?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&Response=json&{params}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            print(f"⚠️ Response was not JSON. Content:\n{response.text[:200]}...")
            return None
    except Exception as e:
        print(f"Error {path}: {e}")
        if 'response' in locals():
             print(f"Response Content: {response.text[:200]}")
        return None

# 1. Test Library/Values (Get Artists)
print("--- Testing Library/Values (Artists) ---")
artists = send_command("Library/Values", "Field=Artist&Limit=5")
print(artists)

# 2. Test Playlists/Add (Create Smartlist)
print("\n--- Testing Playlists/Add (Smartlist) ---")
if artists and 'Values' in artists and artists['Values']:
    test_artist = artists['Values'][0]
    print(f"Creating Smartlist for artist: {test_artist}")
    
    # CreateMode=Overwrite (1)
    playlist_params = f"Type=Smartlist&Name=VoiceCmdTest&Search=[Artist]=[{test_artist}]&CreateMode=1"
    playlist_response = send_command("Playlists/Add", playlist_params)
    print(playlist_response)
else:
    print("No artists found to test smartlist creation.")
