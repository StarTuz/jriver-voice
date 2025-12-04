#!/bin/bash

echo "🎤 JRiver Voice Assistant Installer"
echo "==================================="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    exit 1
fi

# Check for pipx
if ! command -v pipx &> /dev/null; then
    echo "⚠️  pipx is not found. It is recommended for installing python applications."
    echo "   Please install it using your package manager (e.g., sudo pacman -S python-pipx)"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Download Piper TTS
echo "⬇️  Setting up Piper TTS..."
PIPER_DIR="$HOME/jriver-voice/piper"
VOICE_DIR="$HOME/jriver-voice/piper_voices"
mkdir -p "$PIPER_DIR"
mkdir -p "$VOICE_DIR"

# Download Piper binary (Linux x86_64)
if [ ! -f "$PIPER_DIR/piper" ]; then
    echo "   Downloading Piper binary..."
    wget -O piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
    tar -xzf piper.tar.gz -C "$HOME/jriver-voice/"
    rm piper.tar.gz
    echo "   ✅ Piper installed."
else
    echo "   ✅ Piper already installed."
fi

# Download Voice Model (en_GB-cori-high)
VOICE_FILE="$VOICE_DIR/en_GB-cori-high.onnx"
if [ ! -f "$VOICE_FILE" ]; then
    echo "   Downloading voice model (Cori)..."
    wget -O "$VOICE_FILE" https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/en_GB-cori-high.onnx
    wget -O "$VOICE_FILE.json" https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/en_GB-cori-high.onnx.json
    echo "   ✅ Voice model installed."
else
    echo "   ✅ Voice model already installed."
fi

# Install Python Package
echo "📦 Installing JRiver Voice Assistant..."
pipx install . --include-deps --force

echo ""
echo "🎉 Installation Complete!"
echo "   Run 'jriver-voice' to start the assistant."
