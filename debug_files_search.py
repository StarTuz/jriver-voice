import requests
import xml.etree.ElementTree as ET
import urllib.parse

# Configuration
JRIVER_IP = "192.168.254.17"
JRIVER_PORT = "52199"
ACCESS_KEY = "MaDdTJ"
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"

def test_files_search():
    print("Testing Files/Search...")
    
    queries = [
        "[Album]=[Symphony No. 6]",
        "Symphony No. 6",
        "[Album]=[Vaughan Williams: Symphonies Nos. 4 & 6]"
    ]
    
    for q in queries:
        print(f"\nTrying query: {q}")
        encoded_query = urllib.parse.quote(q)
        url = f"{BASE_URL}Files/Search?Query={encoded_query}&Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("Success! Response:")
                print(response.text[:1000]) # Print first 1000 chars
                
                try:
                    root = ET.fromstring(response.text)
                    items = root.findall('Item')
                    print(f"\nFound {len(items)} items/files.")
                    
                    if items:
                        first_item = items[0]
                        print("First item keys/attributes:")
                        for child in first_item:
                            print(f"  {child.tag}: {child.text}")
                        
                        key = first_item.find("Field[@Name='Key']")
                        if key is not None:
                            print(f"  Found Key field: {key.text}")
                except Exception as e:
                    print(f"XML Parsing error: {e}")
            else:
                print("Failed.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_files_search()
