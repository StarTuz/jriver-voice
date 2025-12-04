import requests
import urllib.parse

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def test_special_chars():
    print("Testing Files/Search with special characters...")
    
    # The problematic album name
    album_name = "Vaughan Williams: Symphonies Nos. 4 & 6"
    
    # Test cases
    queries = [
        # 1. Standard encoding (failed before)
        f"[Album]=[{album_name}]",
        
        # 2. Escaping special chars for JRiver search language?
        # JRiver search rules say: "If you want to search for a character that has special meaning, escape it with a backslash."
        # Special chars: [ ] ( ) = < > , - & | / \
        f"[Album]=[Vaughan Williams\: Symphonies Nos. 4 \& 6]",
        
        # 3. Using quotes?
        f'[Album]="{album_name}"',
        
        # 4. Partial match (safer?)
        # Remove special chars and use space (AND) logic?
        # But [Album] field usually expects exact match or substring
        # Let's try substring match without brackets around value?
        # No, [Field]=[Value] is standard.
        
        # 5. Try removing special chars from the value but keeping structure
        # "Vaughan Williams Symphonies Nos 4 6"
        f"[Album]=[Vaughan Williams Symphonies Nos. 4 6]",
        
        # 6. Try just the first part
        f"[Album]=[Vaughan Williams]",
    ]
    
    for q in queries:
        print(f"\nTrying query: {q}")
        encoded_query = urllib.parse.quote(q)
        url = f"{BASE_URL}Files/Search?Query={encoded_query}&Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
        
        try:
            response = requests.get(url, timeout=5)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Success!")
            elif response.status_code == 500:
                print("500 Server Error")
            else:
                print(f"Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_special_chars()
