import requests

JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def debug_search(artist_name):
    print(f"--- Debugging Artist: {artist_name} ---")
    
    # Try 1: Exact match filter
    params = f"Field=Album&Filter=[Artist]=[{artist_name}]"
    url = f"{BASE_URL}Library/Values?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&{params}"
    print(f"Request 1 URL: {url}")
    try:
        r = requests.get(url)
        print(f"Response 1 Code: {r.status_code}")
        print(f"Response 1 Body:\n{r.text[:500]}") # Print first 500 chars
    except Exception as e:
        print(f"Error 1: {e}")

    # Try 2: Partial match (search) if filter fails
    # Library/Values doesn't strictly support 'Search=' in the same way as Library/Files, 
    # but let's see if we can use a different filter syntax.
    
    # Try 3: List ALL albums and see if we can find it manually (sanity check)
    # Warning: This might be huge, so we limit it.
    print("\n--- Sanity Check: Listing first 10 Albums ---")
    params = "Field=Album&Limit=10"
    url = f"{BASE_URL}Library/Values?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}&{params}"
    try:
        r = requests.get(url)
        print(f"Response 3 Body:\n{r.text[:500]}")
    except Exception as e:
        print(f"Error 3: {e}")

if __name__ == "__main__":
    debug_search("Gustav Holst")
    debug_search("gustav holst") # Check case sensitivity
