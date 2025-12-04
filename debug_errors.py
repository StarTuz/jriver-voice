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
        print(f"Response: {r.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")

def debug_filter():
    print("\n--- Debugging Filter: London Symphony Orchestra ---")
    # Test getting albums for this artist
    # Note: requests handles URL encoding of params, but we construct string manually here for print
    # We use requests.get(url, params=...) usually, but here I'm building the string to match the main script style
    
    artist = "London Symphony Orchestra"
    # Try standard filter
    params = f"Field=Album&Filter=[Artist]=[{artist}]"
    send("Library/Values", params)
    
    # Try Album Artist
    params = f"Field=Album&Filter=[Album Artist]=[{artist}]"
    send("Library/Values", params)

def debug_playback_error():
    print("\n--- Debugging Playback Error: Holst: The Planets ---")
    album = "Holst: The Planets, Op. 32"
    
    # 1. Reproduce 500 Error with Smartlist
    print("1. Testing Playlists/Add (Smartlist)...")
    search = f"[Album]=[{album}]"
    # We need to be careful about encoding. The main script uses f-string which puts raw chars in URL.
    # requests.get(url) will encode the path/query if passed as params dict, but if passed as string in url, it might not?
    # Actually requests.get(url) expects a fully formed URL or params dict.
    # The main script does: requests.get(f"{BASE_URL}...{extra_params}")
    # If extra_params contains spaces/commas and isn't encoded, that's the 500 error source!
    
    # Let's try sending it RAW (like the script) to see it fail
    params = f"Type=Smartlist&Name=DebugSmartlist&Search={search}&CreateMode=1"
    send("Playlists/Add", params)
    
    # 2. Test PlayDoctor
    print("\n2. Testing PlayDoctor...")
    params = f"Seed={album}"
    send("Playback/PlayDoctor", params)

if __name__ == "__main__":
    debug_filter()
    debug_playback_error()
