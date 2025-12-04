import pyaudio
import wave
import math
import struct
import sys
import os
import json
import vosk
import time

# Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "mic_test.wav"
MODEL_PATH = "/home/startux/jriver-voice/vosk-model-en-us-0.22-lgraph"

def main():
    p = pyaudio.PyAudio()

    print(f"\n🎤 Microphone Test (Recording for {RECORD_SECONDS} seconds)...")
    print("Please speak a clear sentence like: 'Alice, play some music.'")
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    max_amplitude = 0
    
    # Record
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        # Calculate amplitude manually (audioop removed in Python 3.13)
        count = len(data) // 2
        shorts = struct.unpack("%dh" % count, data)
        sum_squares = sum(s**2 for s in shorts)
        rms = int(math.sqrt(sum_squares / count))
        
        if rms > max_amplitude:
            max_amplitude = rms
            
    print("⏹️  Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save to file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Analyze Volume
    print(f"\n📊 Audio Analysis:")
    print(f"   Max Amplitude: {max_amplitude}")
    
    if max_amplitude < 1000:
        print("   ⚠️  Volume is VERY LOW. Check mic gain or distance.")
    elif max_amplitude < 5000:
        print("   ⚠️  Volume is LOW. You might need to speak up.")
    elif max_amplitude > 30000:
        print("   ⚠️  Volume is TOO HIGH (Clipping). Lower mic gain.")
    else:
        print("   ✅ Volume level looks GOOD.")

    # Test Recognition
    print(f"\n🧠 Testing Recognition with Vosk...")
    if not os.path.exists(MODEL_PATH):
        print(f"   ❌ Model not found at {MODEL_PATH}")
    else:
        vosk.SetLogLevel(-1)
        model = vosk.Model(MODEL_PATH)
        rec = vosk.KaldiRecognizer(model, RATE)
        
        wf = wave.open(WAVE_OUTPUT_FILENAME, "rb")
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        
        result = json.loads(rec.FinalResult())
        text = result.get("text", "")
        print(f"   📝 Heard: '{text}'")

    # Playback
    print(f"\n🔊 Playing back recorded audio...")
    os.system(f"aplay {WAVE_OUTPUT_FILENAME}")
    print("\nDone.")

if __name__ == "__main__":
    main()
