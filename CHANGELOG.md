# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-05-23
### Added
- **"Play Random [Genre]"**: New command to play a random mix of a specific genre (e.g., "Play random Rock") using PlayDoctor.
- **"Play Random"**: Generic command to play a random mix of all music.
- **Global Error Handling**: The application now catches unhandled exceptions in the main loop to prevent crashes.
- **Audio Stream Safety**: Added robust error handling when restarting the microphone stream after speaking.
- **"The" Stripping**: Improved command recognition by ignoring "the" at the start of commands (e.g., "the alice play...").
- **"But" -> "Play"**: Added text normalization to correct "but" to "play" at the start of commands.

### Changed
- **Configuration**: Moved all settings to `~/.config/jriver-voice/config.json`.
- **Setup**: Added an interactive setup wizard for first-time users.
- **Model Loading**: Added `model_manager.py` to automatically download the Vosk model if missing.
- **Project Structure**: Refactored code for open-source release (added `README.md`, `LICENSE`, `install.sh`).

## [0.1.0] - 2024-05-20
### Added
- Initial release.
- Basic voice commands: Play [Artist/Album], Stop, Next, Previous, Pause.
- "Alice" wake word detection.
- JRiver MCWS integration.
- Offline voice recognition with Vosk.
- TTS feedback with Piper.
