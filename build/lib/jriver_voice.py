import vosk
import pyaudio
import json
import requests
import os
import subprocess
import xml.etree.ElementTree as ET
import sys
import difflib
import urllib.parse
import time
from config import cfg

# --- JRiver Configuration ---
# Loaded from config.py
JRIVER_IP = cfg.get("JRIVER_IP")
JRIVER_PORT = cfg.get("JRIVER_PORT")
ACCESS_KEY = cfg.get("ACCESS_KEY")

# Base URL for JRiver Media Center Web Service (MCWS)
BASE_URL = f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/"
# ----------------------------

# --- Wake Word Configuration ---
WAKE_WORD = cfg.get("WAKE_WORD")
# ----------------------------

class VoiceAssistant:
    STATE_LISTENING = 0          # Listening for wake word
    STATE_WAITING_SELECTION = 1  # Waiting for user to select from list
    STATE_COMMAND_MODE = 2       # Wake word detected, listening for commands

    COMMAND_TIMEOUT = cfg.get("COMMAND_TIMEOUT")  # Seconds to wait for command after wake word

    def __init__(self, wake_word=WAKE_WORD):
        self.state = self.STATE_LISTENING
        self.context_items = [] 
        self.current_artist = None
        self.current_field = "Artist"
        self.cache = {} 
        self.stream = None  # Initialize stream to None
        self.wake_word = wake_word.lower()  # Store wake word in lowercase
        self.command_mode_start = None  # Track when command mode started
        self.command_queue = None  # Will be set by main()

    def speak(self, text):
        """Speaks the text using Piper TTS (British Female) or falls back to espeak-ng."""
        print(f"🗣️ Speaking: {text}")
        
        # Pause the microphone stream to prevent hearing ourselves
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            
        # Path to Piper model and binary
        # Look in the source directory (where we downloaded them)
        base_dir = os.path.expanduser("~/jriver-voice")
        model_path = os.path.join(base_dir, "piper_voices", "en_GB-cori-high.onnx")
        piper_binary = os.path.join(base_dir, "piper", "piper")
        
        try:
            # Try using Piper first
            if os.path.exists(model_path) and os.path.exists(piper_binary):
                # echo "text" | ./piper/piper --model model.onnx --output-raw | aplay -r 22050 -f S16_LE -t raw -
                p1 = subprocess.Popen(["echo", text], stdout=subprocess.PIPE)
                p2 = subprocess.Popen([piper_binary, "--model", model_path, "--output-raw"], stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
                subprocess.run(["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-q"], stdin=p2.stdout, check=False)
                p2.wait()
            else:
                # Fallback to espeak-ng
                subprocess.run(["espeak-ng", text], check=False)
                
        except (FileNotFoundError, subprocess.SubprocessError):
            # Fallback if piper/aplay not found
            try:
                subprocess.run(["espeak-ng", text], check=False)
            except FileNotFoundError:
                print("⚠️ espeak-ng not found.")
        finally:
            # Resume microphone stream
            if self.stream and self.stream.is_stopped():
                self.stream.start_stream()

    def send_mcws_command(self, command_path, extra_params="", return_xml=False):
        """Sends a command to JRiver's MCWS API."""
        url = f"{BASE_URL}{command_path}?Zone=-1&ZoneType=ID&Key={ACCESS_KEY}"
        if extra_params:
            url += "&" + extra_params
            
        # Retry logic for connection robustness
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status() 
                print(f"✅ Sent MCWS command: {command_path}")
                
                if return_xml:
                    return response.text
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait 1 second before retrying
                else:
                    print(f"❌ Error sending command to JRiver: {e}")
                    self.speak("I couldn't reach JRiver.")
                    return None
            return None

    def get_all_values(self, field):
        """Fetches ALL values for a field from JRiver and caches them."""
        if field in self.cache:
            return self.cache[field]
            
        print(f"📥 Fetching all {field}s from library...")
        params = f"Field={field}&Limit=10000"
        xml_response = self.send_mcws_command("Library/Values", extra_params=params, return_xml=True)
        
        values = []
        if xml_response:
            try:
                root = ET.fromstring(xml_response)
                values = [item.text for item in root.findall('Item') if item.text]
                self.cache[field] = values
                print(f"   -> Cached {len(values)} {field}s.")
            except ET.ParseError:
                print("❌ Error parsing XML.")
        
        return values

    def normalize_text(self, text):
        """Normalizes spoken text to match library conventions."""
        text = text.lower()
        replacements = {
            "number one": "no. 1", "number two": "no. 2", "number three": "no. 3",
            "number four": "no. 4", "number five": "no. 5", "number six": "no. 6",
            "number seven": "no. 7", "number eight": "no. 8", "number nine": "no. 9",
            "number 1": "no. 1", "number 2": "no. 2", "number 3": "no. 3",
            "number 4": "no. 4", "number 5": "no. 5", "number 6": "no. 6",
            "number 7": "no. 7", "number 8": "no. 8", "number 9": "no. 9",
            " op ": " op. ", " opus ": " op. ",
            "simply": "symphony" 
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    def find_best_match(self, search_term, field="Artist"):
        """
        Uses difflib to find the best fuzzy match.
        Returns (matched_value, score).
        """
        all_values = self.get_all_values(field)
        if not all_values:
            return None, 0
        
        # Phonetic aliases for common artist names that sound different
        # Map common misrecognitions to correct names
        phonetic_aliases = {
            # U2
            "you too": "U2",
            "u two": "U2",
            "you two": "U2",
            "youtube": "U2",
            "a c d c": "AC/DC",
            "eighteen seas": "AC/DC",
            "ac dc": "AC/DC",
            "acdc": "AC/DC",
            
            # Medieval Baebes
            "maybe evil babes": "Mediaeval Baebes",
            "medieval babes": "Mediaeval Baebes",
            "many evil babes": "Mediaeval Baebes",
            "medieval babies": "Mediaeval Baebes",
            "mediaeval babes": "Mediaeval Baebes",

            # Russian/Foreign Composers
            "muzzle sky": "Mussorgsky",
            "muscle ski": "Mussorgsky",
            "rock man enough": "Rachmaninoff",
            "shasta coverage": "Shostakovich",
            "show stock of it": "Shostakovich",
            "prokofiev": "Prokofiev",  # Ensure correct spelling
        }
        
        # Check if search term matches a phonetic alias
        search_lower = search_term.lower()
        if search_lower in phonetic_aliases:
            alias_target = phonetic_aliases[search_lower]
            # Check if the alias exists in the library
            for v in all_values:
                if v.lower() == alias_target.lower():
                    return v, 1.0
            
        # Normalize search term
        search_term = self.normalize_text(search_term)
            
        # 1. Exact Match
        for v in all_values:
            if v.lower() == search_term:
                return v, 1.0
        
        # 2. Substring Match (improved for short queries)
        if len(search_term) <= 4:
            # For very short queries, check if it's similar to a standalone word
            best_word_match = None
            best_word_score = 0
            
            for v in all_values:
                words = v.lower().split()
                for word in words:
                    # Calculate similarity between search term and this word
                    similarity = difflib.SequenceMatcher(None, search_term, word).ratio()
                    if similarity > best_word_score:
                        best_word_score = similarity
                        best_word_match = v
            
            # If we found a very similar standalone word (>0.75), return it
            if best_word_score >= 0.75:
                return best_word_match, 0.95
        
        # Regular substring match
        substring_matches = [v for v in all_values if search_term in v.lower()]
        if substring_matches:
            best_sub = difflib.get_close_matches(search_term, substring_matches, n=1, cutoff=0.0)
            if best_sub:
                return best_sub[0], 0.9

        # 3. Fuzzy Match
        matches = difflib.get_close_matches(search_term, all_values, n=1, cutoff=0.6)
        if matches:
            score = difflib.SequenceMatcher(None, search_term, matches[0].lower()).ratio()
            return matches[0], score
            
        return None, 0

    def play_doctor(self, seed, show_track=True):
        """Plays using Play Doctor with a seed, forcing sequential playback."""
        encoded_seed = urllib.parse.quote(seed)
        params = f"Seed={encoded_seed}&Radio=0"
        self.send_mcws_command("Playback/PlayDoctor", extra_params=params)
        
        # Wait a moment for playback to start, then show what's playing
        if show_track:
            import time
            # Poll for up to 5 seconds for the playlist to populate
            for _ in range(10):
                time.sleep(0.5)
                # Check if playlist is ready
                xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
                if xml_response:
                    try:
                        root = ET.fromstring(xml_response)
                        total_tracks = int(root.find(".//Item[@Name='PlayingNowTracks']").text or 0)
                        if total_tracks > 0:
                            break
                    except:
                        pass
            
            self.what_is_playing_silent()

    def go_to_track(self, track_number):
        """Goes to a specific track number in the current playlist."""
        print(f"Attempting to go to track {track_number}")
        
        # JRiver's Playback/SetPlaylistPosition is 0-indexed
        target_position = track_number - 1 
        
        # Send the command
        self.send_mcws_command("Playback/SetPlaylistPosition", extra_params=f"Position={target_position}")
        
        # Give JRiver a moment to process and update its state
        import time
        time.sleep(0.5) 
        
        # Provide feedback
        # Poll for up to 5 seconds for the playlist to populate
        for _ in range(10):
            time.sleep(0.5)
            # Check if playlist is ready
            xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
            if xml_response:
                try:
                    root = ET.fromstring(xml_response)
                    total_tracks = int(root.find(".//Item[@Name='PlayingNowTracks']").text or 0)
                    if total_tracks > 0:
                        # Wait a moment for JRiver to update
                        time.sleep(1.0)
                        
                        # Get updated status to confirm position
                        xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
                        if xml_response:
                            try:
                                root = ET.fromstring(xml_response)
                                info = {}
                                for item in root.findall('Item'):
                                    info[item.get('Name')] = item.text
                                
                                new_pos = int(info.get('PlayingNowPosition', 0)) + 1 # 0-indexed in API
                                
                                # Call what_is_playing_silent but override the track number announcement
                                # to ensure it matches the playlist position we just navigated to
                                self.what_is_playing_silent(force_track_num=new_pos)
                            except:
                                self.what_is_playing_silent()
                        else:
                            self.what_is_playing_silent()
                        return
                except:
                    pass

    def play_precise_album(self, album_name):
        """Plays exactly the tracks of an album in order."""
        # Note: speak is done by caller to avoid duplicates
        
        # 1. Search for files in this album
        import urllib.parse
        import re
        
        # Try bracket syntax (proper JRiver search format)
        queries_to_try = [f"[Album]=[{album_name}]"]
        
        xml_response = None
        for i, q in enumerate(queries_to_try):
            print(f"Trying album search query ({i+1}/{len(queries_to_try)}): {q}")
            encoded_query = urllib.parse.quote(q)
            # NOTE: Don't add Action=XML - it causes 500 errors!
            temp_response = self.send_mcws_command("Files/Search", extra_params=f"Query={encoded_query}", return_xml=True)
            if temp_response:
                # Check if we actually got results (not just an empty response)
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(temp_response)
                    items = root.findall('Item')
                    if len(items) > 0:
                        print(f"✅ Found {len(items)} tracks with query: {q}")
                        xml_response = temp_response
                        break
                    else:
                        print(f"⚠️  Query returned 0 results, trying next...")
                except:
                    # If we can't parse it, something's wrong, try next query
                    print(f"⚠️  Query returned invalid XML, trying next...")
                    pass
        
        
        if not xml_response:
            self.speak("I couldn't find the album tracks. The album name might have special characters that are difficult to search for.")
            return
            
        try:
            root = ET.fromstring(xml_response)
            tracks = []  # Store (track_num, key) tuples
            
            # Find all Items and collect track number + key
            for item in root.findall('Item'):
                track_num = None
                key = None
                
                for field in item.findall('Field'):
                    field_name = field.get('Name')
                    if field_name == 'Track #':
                        try:
                            track_num = int(field.text)
                        except:
                            track_num = 9999  # Put invalid tracks at end
                    elif field_name == 'Key':
                        key = field.text
                
                if key:
                    # Default to 9999 if no track number found
                    if track_num is None:
                        track_num = 9999
                    tracks.append((track_num, key))
            
            if not tracks:
                self.speak("No tracks found for this album.")
                return
            
            # Sort by track number
            tracks.sort(key=lambda x: x[0])
            keys = [key for _, key in tracks]
                
            print(f"Found {len(keys)} tracks for album {album_name}, sorted by track number")
            
            # 2. Play these keys
            # Join keys with commas (or semicolons? WSDL says "Play a file (or files) by database key")
            # Usually comma or semicolon separated. Let's try comma first.
            keys_str = ",".join(keys)
            
            # Playback/PlayByKey
            # We might need to clear the playlist first? PlayByKey usually replaces Playing Now.
            self.send_mcws_command("Playback/PlayByKey", extra_params=f"Key={keys_str}")
            
            # 3. Show what's playing
            import time
            time.sleep(1)
            self.what_is_playing_silent()
            
        except Exception as e:
            print(f"Error in play_precise_album: {e}")
            self.speak("Something went wrong playing the album.")

    def play_album(self, artist, album, field="Artist"):
        """Plays a specific album using precise playback."""
        self.play_precise_album(album)
        self.state = self.STATE_LISTENING
        self.context_items = []

    def play_generic(self, query):
        """Tries to find the query as an Artist, Composer, or Album and plays it."""
        self.speak(f"Searching for {query}")
        
        # Normalize the query first
        normalized_query = self.normalize_text(query)
        
        # Check if user is asking for a specific work (symphony, concerto, etc.)
        specific_work_keywords = ["symphony", "concerto", "sonata", "quartet", "quintet", 
                                   "no.", "op.", "movement", "adagio", "allegro", "andante"]
        is_specific_work = any(keyword in normalized_query for keyword in specific_work_keywords)
        
        # 1. Search Artists
        artist, artist_score = self.find_best_match(query, field="Artist")
        
        # 2. Search Composers
        composer, composer_score = self.find_best_match(query, field="Composer")
        
        # 3. Search Albums
        album, album_score = self.find_best_match(query, field="Album")
        
        print(f"Scores - Artist: {artist_score:.2f}, Composer: {composer_score:.2f}, Album: {album_score:.2f}")
        
        best_match = None
        match_type = None
        best_score = 0
        
        if artist_score > best_score:
            best_score = artist_score
            best_match = artist
            match_type = "Artist"
            
        if composer_score > best_score:
            best_score = composer_score
            best_match = composer
            match_type = "Composer"
            
        if album_score > best_score:
            best_score = album_score
            best_match = album
            match_type = "Album"
        
        # Decision logic for specific works (symphonies, concertos, etc.)
        if is_specific_work:
            # Find all albums that might contain this work
            all_albums = self.get_all_values("Album")
            
            # Search for albums matching the normalized query
            matching_albums = []
            for alb in all_albums:
                # Check if the album name contains key parts of the query
                if any(word in alb.lower() for word in normalized_query.split() if len(word) > 3):
                    matching_albums.append(alb)
            
            # Use difflib for better matching
            if matching_albums:
                # Score each album
                scored_albums = []
                for alb in matching_albums:
                    score = difflib.SequenceMatcher(None, normalized_query, alb.lower()).ratio()
                    scored_albums.append((alb, score))
                
                # Sort by score and take top matches
                scored_albums.sort(key=lambda x: x[1], reverse=True)
                top_albums = [alb for alb, score in scored_albums[:5] if score > 0.3]
                
                if len(top_albums) == 1:
                    # Only one match, play it
                    self.speak(f"Found {top_albums[0]}")
                    self.play_precise_album(top_albums[0])
                elif len(top_albums) > 1:
                    # Multiple matches - let user choose
                    self.context_items = top_albums
                    self.current_artist = normalized_query  # Store the query for later
                    self.current_field = "SpecificWork"
                    self.state = self.STATE_WAITING_SELECTION
                    
                    display_albums = top_albums[:5]
                    list_text = ", ".join([f"{i+1}. {album}" for i, album in enumerate(display_albums)])
                    
                    self.speak(f"I found {len(top_albums)} albums. {list_text}. Which one?")
                    print(f"Options: {display_albums}")
                else:
                    # No good matches, use raw search
                    self.speak(f"Searching for {normalized_query}.")
                    self.play_doctor(normalized_query)
                # No matches found, use raw search
                self.speak(f"Searching for {normalized_query}.")
                self.play_doctor(normalized_query)
        elif best_match and best_score > 0.8:
            # Special case: if Album score is only slightly higher than Artist/Composer score,
            # prefer Artist/Composer (e.g., "Mozart" the composer vs "Mozart" the album title)
            if match_type == "Album" and max(artist_score, composer_score) > 0.75:
                score_diff = best_score - max(artist_score, composer_score)
                if score_diff < 0.15:  # Very close scores
                    # Prefer Artist or Composer
                    if composer_score >= artist_score:
                        best_match = composer
                        match_type = "Composer"
                    else:
                        best_match = artist
                        match_type = "Artist"
            
            self.speak(f"Found {match_type}: {best_match}")
            if match_type == "Album":
                self.play_precise_album(best_match)
            else:
                self.search_artist_albums(best_match, field=match_type)
        else:
            # Try to see if the query contains both Artist and Album (e.g. "Gustav Holst The Planets")
            # Iterate through cached artists/composers to see if the query starts with one
            found_combined = False
            found_artist_prefix = None
            
            # Use get_all_values to ensure they are loaded
            potential_artists = self.get_all_values("Artist") + self.get_all_values("Composer")
            
            # Sort by length (longest first) to match "London Symphony Orchestra" before "London"
            potential_artists.sort(key=len, reverse=True)
            
            query_lower = normalized_query.lower()
            
            for artist in potential_artists:
                artist_lower = artist.lower()
                # Check if query starts with this artist
                if query_lower.startswith(artist_lower):
                    found_artist_prefix = artist
                    # Check if there's more text after the artist name
                    remaining_text = query_lower[len(artist_lower):].strip()
                    if remaining_text:
                        # This looks like "Artist Album"
                        print(f"Potential combined query: Artist='{artist}', Album='{remaining_text}'")
                        
                        # Search for albums by this artist
                        # We can't use search_artist_albums directly because it lists ALL albums
                        # We need to find the specific album matching remaining_text
                        
                        # 1. Get all albums by this artist using Files/Search (more reliable)
                        encoded_artist = urllib.parse.quote(artist)
                        xml_response = self.send_mcws_command("Files/Search", extra_params=f"Query={encoded_artist}", return_xml=True)
                        
                        artist_albums = []
                        if xml_response:
                            try:
                                root = ET.fromstring(xml_response)
                                items = root.findall('Item')
                                
                                # Collect unique albums from tracks that match this artist
                                albums_set = set()
                                for item in items:
                                    item_artist = None
                                    item_composer = None
                                    item_album = None
                                    
                                    for field_elem in item.findall('Field'):
                                        field_name = field_elem.get('Name')
                                        if field_name == 'Artist':
                                            item_artist = field_elem.text
                                        elif field_name == 'Composer':
                                            item_composer = field_elem.text
                                        elif field_name == 'Album':
                                            item_album = field_elem.text
                                    
                                    # Check if artist matches (Artist or Composer)
                                    is_match = False
                                    if item_artist and artist.lower() in item_artist.lower():
                                        is_match = True
                                    elif item_composer and artist.lower() in item_composer.lower():
                                        is_match = True
                                        
                                    if is_match and item_album:
                                        albums_set.add(item_album)
                                
                                artist_albums = list(albums_set)
                            except:
                                pass
                        
                        if artist_albums:
                            # 2. Find best match for remaining_text in these albums
                            candidates = []
                            
                            for alb in artist_albums:
                                # Check for substring match first (common in classical: "Holst: The Planets...")
                                if remaining_text.lower() in alb.lower():
                                    # Boost score for substring match
                                    score = 0.9
                                else:
                                    score = difflib.SequenceMatcher(None, remaining_text, alb.lower()).ratio()
                                
                                if score > 0.5:
                                    candidates.append((alb, score))
                            
                            # Sort candidates by score
                            candidates.sort(key=lambda x: x[1], reverse=True)
                            
                            if candidates:
                                if len(candidates) == 1:
                                    best_alb = candidates[0][0]
                                    self.speak(f"Found {best_alb} by {artist}")
                                    self.play_precise_album(best_alb)
                                else:
                                    # Multiple matches - let user choose
                                    top_candidates = [c[0] for c in candidates[:10]]
                                    self.context_items = top_candidates
                                    self.current_artist = artist
                                    self.current_field = "Album"
                                    self.state = self.STATE_WAITING_SELECTION
                                    
                                    list_text = ", ".join([f"{i+1}. {alb}" for i, alb in enumerate(top_candidates)])
                                    self.speak(f"I found {len(candidates)} albums by {artist}. {list_text}. Which one?")
                                    print(f"Options: {top_candidates}")
                                    
                                found_combined = True
                                break
            
            # Fallback: If we identified an artist but couldn't find tracks/albums by them
            # (e.g. "Gustav Holst" is in Album title but not in Artist/Composer field)
            if not found_combined and found_artist_prefix:
                 # Try to find an album that matches the remaining text AND contains the artist name
                 # or parts of the artist name
                 print(f"Fallback: Searching album cache for '{remaining_text}' with artist context '{found_artist_prefix}'")
                 all_albums = self.get_all_values("Album")
                 
                 fallback_candidates = []
                 
                 for alb in all_albums:
                     # Check if remaining text matches
                     if remaining_text.lower() in alb.lower():
                         # Check if artist name (or last name) is in the album title
                         # Split artist name into parts (e.g. "Gustav", "Holst")
                         artist_parts = found_artist_prefix.lower().split()
                         
                         # Check if ANY significant part of the artist name is in the album title
                         # (e.g. "Holst" in "Holst: The Planets")
                         if any(part in alb.lower() for part in artist_parts if len(part) > 2):
                             # Good candidate
                             # Boost score if remaining text is a substring
                             if remaining_text.lower() in alb.lower():
                                 score = 0.9
                             else:
                                 score = difflib.SequenceMatcher(None, remaining_text, alb.lower()).ratio()
                                 
                             if score > 0.6:
                                 fallback_candidates.append((alb, score))
                 
                 # Sort candidates by score
                 fallback_candidates.sort(key=lambda x: x[1], reverse=True)
                 
                 if fallback_candidates:
                     if len(fallback_candidates) == 1:
                         best_alb = fallback_candidates[0][0]
                         self.speak(f"Found {best_alb}")
                         self.play_precise_album(best_alb)
                     else:
                         # Multiple matches - let user choose
                         top_candidates = [c[0] for c in fallback_candidates[:10]]
                         self.context_items = top_candidates
                         self.current_artist = found_artist_prefix
                         self.current_field = "Album"
                         self.state = self.STATE_WAITING_SELECTION
                         
                         list_text = ", ".join([f"{i+1}. {alb}" for i, alb in enumerate(top_candidates)])
                         self.speak(f"I found {len(fallback_candidates)} albums. {list_text}. Which one?")
                         print(f"Options: {top_candidates}")
                         
                     found_combined = True
            
            if not found_combined:
                self.speak(f"I couldn't find an exact match, so I'll search for {normalized_query}.")
                self.play_doctor(normalized_query)

    def search_artist_albums(self, artist_name, field="Artist"):
        """Searches for albums by the given artist/composer."""
        # JRiver's Library/Values filtering doesn't work reliably
        # Instead, use Files/Search to find tracks by this artist, then get unique albums
        print(f"Searching for albums by {field}: {artist_name}")
        
        query = urllib.parse.quote(artist_name)
        xml_response = self.send_mcws_command("Files/Search", extra_params=f"Query={query}", return_xml=True)
        
        if not xml_response:
            self.speak(f"I found {artist_name}, but couldn't search for albums.")
            return

        try:
            root = ET.fromstring(xml_response)
            items = root.findall('Item')
            
            # Collect unique albums from tracks that match this artist
            albums_set = set()
            for item in items:
                item_field_value = None
                item_album = None
                
                for field_elem in item.findall('Field'):
                    field_name = field_elem.get('Name')
                    if field_name == field:  # Could be 'Artist' or 'Composer'
                        item_field_value = field_elem.text
                    elif field_name == 'Album':
                        item_album = field_elem.text
                
                # Include album if:
                # 1. The artist/composer name is in the respective field, OR
                # 2. The artist/composer name is in the Album title (common for classical music)
                if item_album:
                    if item_field_value and artist_name.lower() in item_field_value.lower():
                        albums_set.add(item_album)
                    elif artist_name.lower() in item_album.lower():
                        # Also include if artist name is in the album title
                        albums_set.add(item_album)
            
            albums = sorted(list(albums_set))
            
            if not albums:
                self.speak(f"I found {artist_name}, but couldn't find any albums in the library.")
                return

            if len(albums) == 1:
                self.play_album(artist_name, albums[0], field)
            else:
                self.context_items = albums
                self.current_artist = artist_name
                self.current_field = field
                self.state = self.STATE_WAITING_SELECTION
                
                display_albums = albums[:10]
                list_text = ", ".join([f"{i+1}. {album}" for i, album in enumerate(display_albums)])
                
                self.speak(f"I found {len(albums)} albums. {list_text}. Which one?")
                print(f"Options: {display_albums}")

        except ET.ParseError:
            self.speak("Error reading library data.")

    def handle_selection(self, text):
        """Handles user selection from a list."""
        # Handle British pronunciations
        british_pronunciations = {
            "for": "four",
            "to": "two", 
            "too": "two",
            "tree": "three",
            "ate": "eight",
        }
        
        # Apply British pronunciation corrections
        words = text.split()
        corrected_words = [british_pronunciations.get(word, word) for word in words]
        text = " ".join(corrected_words)
        
        word_map = {
            "one": 0, "first": 0, "1": 0,
            "two": 1, "second": 1, "2": 1,
            "three": 2, "third": 2, "3": 2,
            "four": 3, "fourth": 3, "4": 3,
            "five": 4, "fifth": 4, "5": 4,
            "six": 5, "sixth": 5, "6": 5,
            "seven": 6, "seventh": 6, "7": 6,
            "eight": 7, "eighth": 7, "8": 7,
            "nine": 8, "ninth": 8, "9": 8,
            "ten": 9, "tenth": 9, "10": 9
        }
        
        selection_index = -1
        for word, index in word_map.items():
            if word in text:
                selection_index = index
                break
        
        if selection_index >= 0 and selection_index < len(self.context_items):
            selected_album = self.context_items[selection_index]
            field = getattr(self, 'current_field', 'Artist')
            
            if field == "SpecificWork":
                # User selected an album containing a specific work
                # Use precise playback to encourage starting at track 1
                self.speak(f"Playing {selected_album}")
                self.play_precise_album(selected_album)
                self.state = self.STATE_LISTENING
                self.context_items = []
            else:
                # User selected an album from artist/composer search
                self.play_album(self.current_artist, selected_album, field)
        elif "cancel" in text or "stop" in text:
            self.speak("Selection cancelled.")
            self.state = self.STATE_LISTENING
            self.context_items = []
        else:
            self.speak("Please say a number like one, two, or three.")

    def go_to_track(self, track_number):
        """Navigate to a specific track number in the current Playing Now playlist."""
        # Special case: if requesting track 1, go to the very beginning
        # (This helps when user wants to start an album from the beginning)
        if track_number == 1:
            # Jump to the beginning of the Playing Now playlist
            xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
            if not xml_response:
                return
            
            try:
                root = ET.fromstring(xml_response)
                info = {}
                for item in root.findall('Item'):
                    info[item.get('Name')] = item.text
                
                current_pos = int(info.get('PlayingNowPosition', 0))
                
                if current_pos == 0:
                    self.speak(f"Already at the beginning.")
                    # Still show what's playing
                    self.what_is_playing_silent()
                    return
                else:
                    self.speak(f"Going to the beginning.")
                    # Go back to position 0
                    for _ in range(current_pos):
                        self.send_mcws_command("Playback/Previous")
                    # Show what's now playing
                    self.what_is_playing_silent()
                    return
                    
            except Exception as e:
                print(f"Error: {e}")
                self.speak("I couldn't go to the beginning.")
                return
        
        # For other track numbers, use relative navigation
        xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
        if not xml_response:
            return
        
        try:
            root = ET.fromstring(xml_response)
            info = {}
            for item in root.findall('Item'):
                info[item.get('Name')] = item.text
            
            current_pos = int(info.get('PlayingNowPosition', 0))
            total_tracks = int(info.get('PlayingNowTracks', 0))
            
            # If total_tracks is 0, the playlist might not be loaded yet
            if total_tracks == 0:
                self.speak(f"The playlist is still loading. Try again in a moment.")
                return
            
            if track_number < 1 or track_number > total_tracks:
                self.speak(f"Track {track_number} is out of range. There are {total_tracks} tracks.")
                return
            
            # Calculate how many times to press next/previous
            target_pos = track_number - 1  # 0-indexed
            offset = target_pos - current_pos
            
            if offset == 0:
                self.speak(f"Already on track {track_number}.")
                self.what_is_playing_silent()
                return
            elif offset > 0:
                # Go forward
                self.speak(f"Going to track {track_number}.")
                for _ in range(offset):
                    self.send_mcws_command("Playback/Next")
                # Show what's now playing (wait for JRiver to update)
                import time
                time.sleep(0.5)
                self.what_is_playing_silent()
            else:
                # Go backward
                self.speak(f"Going to track {track_number}.")
                for _ in range(abs(offset)):
                    self.send_mcws_command("Playback/Previous")
                # Show what's now playing (wait for JRiver to update)
                import time
                time.sleep(0.5)
                self.what_is_playing_silent()
                    
        except Exception as e:
            print(f"Error in go_to_track: {e}")
            self.speak("I couldn't navigate to that track.")

    def what_is_playing_silent(self, force_track_num=None):
        """Shows what's playing without speaking (just prints)."""
        xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
        if not xml_response:
            return
            
        try:
            root = ET.fromstring(xml_response)
            info = {}
            for item in root.findall('Item'):
                info[item.get('Name')] = item.text
            
            name = info.get('Name', 'Unknown Track')
            artist = info.get('Artist', 'Unknown Artist')
            file_key = info.get('FileKey')
            position = int(info.get('PlayingNowPosition', 0)) + 1  # 1-indexed
            total = info.get('PlayingNowTracks', '?')
            
            # Use forced track number if provided (for accurate navigation feedback)
            display_pos = force_track_num if force_track_num is not None else position
            
            # Get track number from file info
            track_num = "?"
            if file_key and file_key != '-1':  # Validate file key before using it
                file_info = self.send_mcws_command("File/GetInfo", extra_params=f"File={file_key}", return_xml=True)
                if file_info:
                    try:
                        file_root = ET.fromstring(file_info)
                        for field in file_root.findall('.//Field'):
                            if field.get('Name') == 'Track #':
                                track_num = field.text
                                break
                    except:
                        pass
            
            print(f"\n🎵 Now Playing (Track {display_pos} of {total}):")
            print(f"   Album Track #: {track_num}")
            print(f"   Title: {name}")
            print(f"   Artist: {artist}\n")
            
        except Exception as e:
            print(f"Error getting track info: {e}")

    def what_is_playing(self):
        """Announces the currently playing track with track number info."""
        xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
        if not xml_response:
            return
            
        try:
            root = ET.fromstring(xml_response)
            info = {}
            for item in root.findall('Item'):
                info[item.get('Name')] = item.text
            
            name = info.get('Name', 'Unknown Track')
            artist = info.get('Artist', 'Unknown Artist')
            file_key = info.get('FileKey')
            
            # Build response
            response = f"Playing {name} by {artist}"
            
            # Try to get track number info
            if file_key and file_key != '-1':  # Validate file key before using it
                file_info = self.send_mcws_command("File/GetInfo", extra_params=f"File={file_key}", return_xml=True)
                if file_info:
                    try:
                        file_root = ET.fromstring(file_info)
                        # File/GetInfo returns <Field Name="..."> tags
                        track_num = None
                        disc_num = None
                        
                        for field in file_root.findall('.//Field'):
                            field_name = field.get('Name')
                            if field_name == 'Track #':
                                track_num = field.text
                            elif field_name == 'Disc #':
                                disc_num = field.text
                        
                        if track_num:
                            if disc_num and disc_num != '1':
                                response += f", track {track_num} of disc {disc_num}"
                            else:
                                response += f", track {track_num}"
                    except:
                        pass
            
            response += "."
            self.speak(response)
            
        except Exception as e:
            print(f"Error in what_is_playing: {e}")
            self.speak("I couldn't get playback info.")

    def list_tracks(self):
        """Lists information about the current Playing Now playlist."""
        xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
        if not xml_response:
            return
        
        try:
            root = ET.fromstring(xml_response)
            info = {}
            for item in root.findall('Item'):
                info[item.get('Name')] = item.text
            
            current_pos = int(info.get('PlayingNowPosition', 0)) + 1  # 1-indexed
            total_tracks = int(info.get('PlayingNowTracks', 0))
            
            if total_tracks == 0:
                print("\n❌ No tracks in Playing Now playlist.\n")
                self.speak("The playlist is empty.")
                return
            
            print(f"\n📋 Playing Now Playlist ({total_tracks} tracks):")
            print(f"   Current position: {current_pos} of {total_tracks}\n")
            
            # Get the actual playlist
            playlist_xml = self.send_mcws_command("Playback/Playlist", return_xml=True)
            if playlist_xml:
                try:
                    playlist_root = ET.fromstring(playlist_xml)
                    tracks = []
                    for item in playlist_root.findall('Item'):
                        track_info = {}
                        for field in item.findall('Field'):
                            field_name = field.get('Name')
                            if field_name in ['Name', 'Track #']:
                                track_info[field_name] = field.text
                        
                        track_num = track_info.get('Track #', '?')
                        track_name = track_info.get('Name', 'Unknown Track')
                        tracks.append((track_num, track_name))
                    
                    # Display tracks (limit to 20 for readability)
                    display_count = min(20, len(tracks))
                    for i, (track_num, track_name) in enumerate(tracks[:display_count], 1):
                        marker = "▶" if i == current_pos else " "
                        print(f"   {marker} {i}. {track_name}")
                    
                    if len(tracks) > display_count:
                        print(f"\n   ... and {len(tracks) - display_count} more tracks")
                    
                    print(f"\n   Say 'play track [number]' to jump to any track\n")
                    
                except Exception as e:
                    print(f"   Error parsing playlist: {e}\n")
            
            self.speak(f"There are {total_tracks} tracks in the playlist. You're at position {current_pos}.")
            
        except Exception as e:
            print(f"Error listing tracks: {e}")
            self.speak("I couldn't get playlist info.")

    def process_command(self, text):
        """Maps spoken text to commands."""
        text = text.lower().strip()
        
        # Clean up common artifacts from voice recognition
        text = text.strip()
        while text.startswith("the "):
            text = text[4:]
        while text.endswith(" the"):
            text = text[:-4]
        text = text.strip()
        
        print(f"📝 Processing: '{text}' (State: {self.state})")

        # When waiting for selection, don't require wake word
        if self.state == self.STATE_WAITING_SELECTION:
            self.handle_selection(text)
            return

        # Check if command mode has timed out
        if self.state == self.STATE_COMMAND_MODE:
            if time.time() - self.command_mode_start > self.COMMAND_TIMEOUT:
                print(f"⏱️ Command mode timed out, returning to wake word listening")
                self.state = self.STATE_LISTENING
                self.command_mode_start = None

        # If in listening mode, check for wake word
        if self.state == self.STATE_LISTENING:
            # Wake word aliases (common misrecognitions)
            wake_word_aliases = [
                "less", "ls", "alex", "else", "allis", "palace", "at us", "at by", "a list", "analysis"
            ]
            
            # Check for wake word or aliases
            detected_wake_word = None
            if text.startswith(self.wake_word):
                detected_wake_word = self.wake_word
            else:
                for alias in wake_word_aliases:
                    if text.startswith(alias):
                        detected_wake_word = alias
                        break
            
            if not detected_wake_word:
                print(f"🤷 Ignored (no wake word): {text}")
                return
            
            # Clear any pending commands in the queue when wake word is detected
            if self.command_queue:
                cleared = 0
                while not self.command_queue.empty():
                    try:
                        self.command_queue.get_nowait()
                        cleared += 1
                    except:
                        break
                if cleared > 0:
                    print(f"🧹 Cleared {cleared} stale command(s) from queue")
            
            # Strip wake word from command
            text = text[len(detected_wake_word):].strip()
            print(f"✅ Wake word detected! Command: '{text}'")
            
            # If no command after wake word, enter command mode
            if not text:
                self.state = self.STATE_COMMAND_MODE
                self.command_mode_start = time.time()
                self.speak("Yes?")
                print(f"🎤 Entered command mode (5 second window)")
                return
        
        elif self.state == self.STATE_COMMAND_MODE:
            # In command mode, accept any command (refresh timeout)
            self.command_mode_start = time.time()
            print(f"✅ Command received in command mode: '{text}'")

        # Process the command (whether from wake word or command mode)
        
        # More robust quit detection - check if quit/exit appears anywhere
        if "quit" in text or "exit" in text or "stop listening" in text:
            self.send_mcws_command("Playback/Stop")  # Stop playback before quitting
            self.speak("Goodbye.")
            raise KeyboardInterrupt

        elif "pause" in text:
            self.send_mcws_command("Playback/Pause")
            
        elif "stop" in text:
            self.send_mcws_command("Playback/Stop")
            
        elif text in ["play", "resume", "start music"]:
            self.send_mcws_command("Playback/Play")

        # Check for navigation commands with various phrasings
        elif "next track" in text or "next song" in text or text in ["next", "skip"]:
            self.send_mcws_command("Playback/Next")
            time.sleep(0.5)  # Give JRiver a moment to update
            self.what_is_playing_silent()

        elif "previous track" in text or "previous song" in text or text in ["previous", "back"]:
            self.send_mcws_command("Playback/Previous")
            time.sleep(0.5)  # Give JRiver a moment to update
            self.what_is_playing_silent()
            
        elif "volume up" in text:
            self.send_mcws_command("Playback/Volume", extra_params="Level=600")
            
        elif "volume down" in text:
            self.send_mcws_command("Playback/Volume", extra_params="Level=400")

        elif text in ["turn it off", "shut down", "stop all"]:
            self.send_mcws_command("Playback/StopAll")
            self.speak("Stopping all playback.")

        elif "what is playing" in text or "what song is this" in text or "what track is this" in text or "what's playing" in text or "what song" in text or "what track" in text:
            self.what_is_playing()

        elif "list tracks" in text or "show tracks" in text or "show playlist" in text:
            self.list_tracks()

        elif "go to track" in text or "jump to track" in text or "play track" in text or "play truck" in text or "play crack" in text or "play black" in text or "play check" in text:
            # Extract track number from command
            # Only proceed if there's actually a number mentioned
            words = text.split()
            track_num = None
            
            # Look for number words or digits
            number_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
                         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
            
            # Check if any number word or digit is present
            has_number = any(word in number_map or word.isdigit() for word in words)
            
            if not has_number:
                # This might be "play track" without a number, ignore it
                print(f"🤷 Ignored: {text}")
            else:
                # Extract the number
                for word in words:
                    if word in number_map:
                        track_num = number_map[word]
                        break
                    elif word.isdigit():
                        track_num = int(word)
                        break
                
                if track_num:
                    self.go_to_track(track_num)
                else:
                    self.speak("Please say which track number.")

        # --- Explicit Search Commands ---
        elif text.startswith("play artist") or text.startswith("find artist") or text.startswith("search for artist"):
            for prefix in ["play artist", "find artist", "search for artist"]:
                if text.startswith(prefix):
                    query = text.replace(prefix, "").strip()
                    if query:
                        artist, a_score = self.find_best_match(query, "Artist")
                        composer, c_score = self.find_best_match(query, "Composer")
                        
                        best = artist if a_score >= c_score else composer
                        field = "Artist" if a_score >= c_score else "Composer"
                        
                        if best and max(a_score, c_score) > 0.6:
                            self.speak(f"Found {field}: {best}")
                            self.search_artist_albums(best, field)
                        else:
                            self.speak(f"I couldn't find artist {query}")
                    else:
                        self.speak("Please say the artist name.")
                    return

        elif text.startswith("play album") or text.startswith("find album") or text.startswith("search for album"):
            for prefix in ["play album", "find album", "search for album"]:
                if text.startswith(prefix):
                    query = text.replace(prefix, "").strip()
                    if query:
                        album, score = self.find_best_match(query, "Album")
                        if album and score > 0.6:
                            self.speak(f"Playing {album}")
                            self.play_precise_album(album)
                        else:
                            self.speak(f"I couldn't find album {query}")
                    else:
                        self.speak("Please say the album name.")
                    return

        elif text.startswith("search for "):
            query = text.replace("search for ", "").strip()
            if query:
                self.play_generic(query)
            else:
                self.speak("Please say what to search for.")

        elif text == "list commands":
            print("Commands: play [anything], stop, next, quit, what's playing")
            self.speak("You can say play [artist or album], stop, next, quit, or what's playing.")

        # --- Generic Play Command ---
        elif text.startswith("play "):
            query = text.replace("play ", "").strip()
            if query:
                # Check if it's just a number - if so, treat as track navigation
                # (only if music is already playing)
                number_words = {
                    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10
                }
                
                if query.lower() in number_words:
                    # Check if music is playing
                    xml_response = self.send_mcws_command("Playback/Info", return_xml=True)
                    if xml_response:
                        try:
                            root = ET.fromstring(xml_response)
                            info = {}
                            for item in root.findall('Item'):
                                info[item.get('Name')] = item.text
                            
                            total_tracks = int(info.get('PlayingNowTracks', 0))
                            if total_tracks > 0:
                                # Music is playing, interpret as track navigation
                                track_num = number_words[query.lower()]
                                self.go_to_track(track_num)
                                return
                        except:
                            pass  # If error, fall through to normal play
                
                # Not a number or no music playing, treat as normal search
                self.play_generic(query)
            else:
                self.send_mcws_command("Playback/Play")

        else:
            print(f"🤷 Ignored: {text}")

# --- Main Execution ---

import threading
import queue

def command_worker(assistant, command_queue):
    """Worker thread to process commands from the queue."""
    while True:
        text = command_queue.get()
        if text is None:
            break
        try:
            assistant.process_command(text)
        except KeyboardInterrupt:
            # Handle quit command from worker
            os._exit(0)
        except Exception as e:
            print(f"Error processing command: {e}")
        finally:
            command_queue.task_done()

def main():
    # Check if setup is needed
    if not ACCESS_KEY:
        print("⚠️  No Access Key found.")
        if not cfg.setup_wizard():
            print("❌ Setup cancelled. Exiting.")
            sys.exit(1)
            
    MODEL_PATH = cfg.get("VOSK_MODEL_PATH")
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 4096  # Reduced from 8192 for lower latency

    # Ensure model exists (auto-download if needed)
    import model_manager
    if not model_manager.setup_vosk_model(MODEL_PATH):
        sys.exit(1)

    # Check JRiver connectivity
    print("Checking JRiver connection...")
    try:
        requests.get(f"http://{JRIVER_IP}:{JRIVER_PORT}/MCWS/v1/Alive", timeout=2)
        print("✅ JRiver is running.")
    except requests.exceptions.ConnectionError:
        print("⚠️  JRiver is not running. Attempting to launch...")
        try:
            subprocess.Popen(["mediacenter35"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("⏳ Waiting for JRiver to start (15s)...")
            time.sleep(15)
        except FileNotFoundError:
            print("❌ Could not launch 'mediacenter35'. Please start JRiver manually.")
            
    model = vosk.Model(MODEL_PATH)
    assistant = VoiceAssistant()
    
    # Start command processing thread
    command_queue = queue.Queue()
    assistant.command_queue = command_queue  # Give assistant access to queue for clearing
    worker = threading.Thread(target=command_worker, args=(assistant, command_queue), daemon=True)
    worker.start()
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    assistant.stream = stream  # Assign stream to assistant so it can pause/resume it
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)

    print("\n--- JRiver Voice Assistant Ready ---")
    assistant.speak("I am ready.")

    try:
        while True:
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text")
                    if text:
                        # Offload processing to worker thread
                        command_queue.put(text)
            except OSError as e:
                if e.errno == -9983 or "Stream is stopped" in str(e):
                    # Stream paused (likely speaking), wait a bit and retry
                    time.sleep(0.1)
                    continue
                elif e.errno == -9988 or "Stream closed" in str(e):
                    # Stream closed (likely quitting), break out of loop
                    break
                else:
                    raise e
                    
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
