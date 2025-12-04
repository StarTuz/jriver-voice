import difflib

# Simulated values from the user's library (based on previous logs)
albums = [
    "Vaughan Williams: Symphony No. 6 / The Lark Ascending",
    "Vaughan Williams: Symphony No. 6, Fantasia on a theme by Thomas Tallis, The Lark Ascending",
    "VAUGHAN WILLIAMS: Symphonies Nos. 6 and 8 / Nocturne",
    "Symphony No. 6 (Pathétique)",
    "Holst: The Planets, Op. 32"
]

artists = [
    "Ralph Vaughan Williams",
    "Vaughan Williams",
    "London Symphony Orchestra"
]

def test_match(query):
    print(f"Query: '{query}'")
    
    # Normalization (Simple)
    normalized = query.lower().replace("number", "no.").replace(" one", " 1").replace(" two", " 2").replace(" three", " 3").replace(" four", " 4").replace(" five", " 5").replace(" six", " 6").replace(" seven", " 7").replace(" eight", " 8").replace(" nine", " 9")
    print(f"Normalized: '{normalized}'")
    
    # Check Albums
    print("--- Albums ---")
    matches = difflib.get_close_matches(normalized, albums, n=3, cutoff=0.4)
    for m in matches:
        s = difflib.SequenceMatcher(None, normalized, m.lower()).ratio()
        print(f"Match: '{m}' (Score: {s:.2f})")

    # Check Artists
    print("--- Artists ---")
    matches = difflib.get_close_matches(normalized, artists, n=3, cutoff=0.4)
    for m in matches:
        s = difflib.SequenceMatcher(None, normalized, m.lower()).ratio()
        print(f"Match: '{m}' (Score: {s:.2f})")

if __name__ == "__main__":
    test_match("vaughan williams symphony number six")
