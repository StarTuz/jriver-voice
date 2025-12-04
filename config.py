import os
import json
import pathlib

# Default Configuration
DEFAULTS = {
    "JRIVER_IP": "localhost",
    "JRIVER_PORT": 52199,
    "ACCESS_KEY": "",
    "WAKE_WORD": "Alice",
    "VOSK_MODEL_PATH": str(pathlib.Path.home() / "jriver-voice" / "vosk-model-en-us-0.22-lgraph"),
    "COMMAND_TIMEOUT": 5
}

CONFIG_DIR = pathlib.Path.home() / ".config" / "jriver-voice"
SYSTEM_CONFIG_FILE = CONFIG_DIR / "config.json"
# Check CWD and Module directory
CWD_CONFIG_FILE = pathlib.Path("config.json")
MODULE_CONFIG_FILE = pathlib.Path(__file__).parent / "config.json"

class Config:
    def __init__(self):
        self._config = DEFAULTS.copy()
        
        # Determine which config file to use
        if CWD_CONFIG_FILE.exists():
            self.config_file = CWD_CONFIG_FILE
        elif MODULE_CONFIG_FILE.exists():
            self.config_file = MODULE_CONFIG_FILE
        else:
            self.config_file = SYSTEM_CONFIG_FILE
            
        self.load()

    def load(self):
        """Load config from file and environment variables."""
        # 1. Load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
                    print(f"✅ Loaded config from: {self.config_file}")
            except json.JSONDecodeError:
                print(f"⚠️  Error reading config file at {self.config_file}. Using defaults.")
        else:
            print(f"⚠️  Config file not found at {self.config_file}. Using defaults.")
            print(f"   Default VOSK_MODEL_PATH: {self._config['VOSK_MODEL_PATH']}")

        # 2. Override with Environment Variables
        for key in self._config:
            env_val = os.environ.get(f"JRIVER_{key}") or os.environ.get(key)
            if env_val:
                # Handle types (int vs string)
                if isinstance(self._config[key], int):
                    try:
                        self._config[key] = int(env_val)
                    except ValueError:
                        pass
                else:
                    self._config[key] = env_val

    def save(self):
        """Save current config to file."""
        # If using system config, ensure dir exists
        if self.config_file == SYSTEM_CONFIG_FILE:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
        with open(self.config_file, "w") as f:
            json.dump(self._config, f, indent=4)
        print(f"✅ Configuration saved to {self.config_file}")

    def get(self, key):
        return self._config.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self._config[key] = value

    def setup_wizard(self):
        """Interactive setup wizard for first run."""
        print("\n👋 Welcome to JRiver Voice Assistant Setup!")
        print("-------------------------------------------")
        print("We need a few details to connect to JRiver Media Center.\n")

        # Access Key
        current_key = self.get("ACCESS_KEY")
        key = input(f"Enter JRiver Access Key [{current_key}]: ").strip()
        if key:
            self.set("ACCESS_KEY", key)
        elif not current_key:
            print("❌ Access Key is required.")
            return False

        # IP Address
        current_ip = self.get("JRIVER_IP")
        ip = input(f"Enter JRiver IP Address [{current_ip}]: ").strip()
        if ip:
            self.set("JRIVER_IP", ip)

        # Wake Word
        current_wake = self.get("WAKE_WORD")
        wake = input(f"Enter Wake Word [{current_wake}]: ").strip()
        if wake:
            self.set("WAKE_WORD", wake)

        self.save()
        print("\n✅ Setup complete! You can change these settings later in:")
        print(f"   {self.config_file}\n")
        return True

# Global instance
cfg = Config()
