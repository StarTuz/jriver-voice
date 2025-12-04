# JRiver Voice Assistant

A privacy-focused, offline voice assistant for JRiver Media Center on Linux. Control your music library with natural voice commands, without sending audio to the cloud. Prompted and teted with Gemini 3/Claude Sonnet 4.5 (Thinking) under Gemini Antigravity IDE. 

## Features

*   **Offline Recognition:** Uses Vosk for fast, local speech-to-text.
*   **Natural TTS:** High-quality British female voice (Piper TTS).
*   **Smart Matching:** Fuzzy search for artists, albums, and composers.
*   **Wake Word:** "Alice" (configurable) with command timeout.
*   **Robust:** Auto-launches JRiver, handles connection retries, and clears stale commands.
*   **Privacy:** No audio leaves your machine.

## System Requirements

*   **OS:** Linux (Tested on Arch/Manjaro)
*   **Python:** 3.9+
*   **JRiver Media Center:** Version 30+ (Running and MCWS enabled)
*   **Microphone:** Working audio input (ALSA/PulseAudio)

### Dependencies
You need to install a few system packages before running the assistant:

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python-pipx ffmpeg espeak-ng portaudio
```

**Debian / Ubuntu:**
```bash
sudo apt install pipx ffmpeg espeak-ng portaudio19-dev python3-dev
```

**Piper TTS:**
The assistant uses Piper for speech. The install script will handle downloading the binary and voice model for you.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/jriver-voice.git
    cd jriver-voice
    ```

2.  **Run the installer:**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

3.  **First Run:**
    ```bash
    jriver-voice
    ```
    The first time you run it, a setup wizard will ask for your:
    *   JRiver Access Key (Options > Media Network > Access Key)
    *   JRiver IP Address (usually `localhost` if running on the same machine)

    It will also automatically download the Vosk voice recognition model (~128MB).

## Usage

Say **"Alice"** to wake up the assistant. Wait for the "Yes?" response, then speak your command.

### Common Commands
*   **"Play [Artist]"** - *e.g., "Play Pink Floyd"*
*   **"Play [Album]"** - *e.g., "Play Dark Side of the Moon"*
*   **"Play [Composer]"** - *e.g., "Play Beethoven"*
*   **"Next track"** / **"Previous track"**
*   **"Pause"** / **"Stop"** / **"Resume"**
*   **"What is playing?"**
*   **"List tracks"** - *Lists tracks on the current album*
*   **"Search for [Query]"** - *Generic search*
*   **"Quit"** - *Stops playback and exits the assistant*

## Configuration

Settings are stored in `~/.config/jriver-voice/config.json`. You can edit this file to change:
*   `WAKE_WORD`: Change "Alice" to something else.
*   `COMMAND_TIMEOUT`: How long to wait for a command (default: 5s).
*   `JRIVER_IP` / `PORT`: Connection details.

## Troubleshooting

*   **"Vosk model not found":** Run `jriver-voice` again, and it should offer to download it.
*   **Microphone issues:** Ensure your microphone is set as the default input device in your OS sound settings.
*   **JRiver not connecting:** Make sure Media Network is enabled in JRiver Options and the Access Key is correct.

## License

MIT License. See `LICENSE` for details.
