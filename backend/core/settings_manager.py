
import json
import os
import logging
from typing import Dict, Any, Optional
from core.config import DATA_DIR

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "system": {
        "language": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "log_level": "INFO",
        "max_concurrent_tasks": 3
    },
    "integrations": {
        "openai_api_key": "",
        "groq_api_key": "",
        "tiktok_cookie_path": "cookies.json"
    },
    "niche": {
        "default_niche": "General",
        "auto_detect": True
    }
}

class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Loads settings from JSON, creating default if missing."""
        if not os.path.exists(SETTINGS_FILE):
            logger.info("Settings file not found. Creating defaults.")
            self.settings = DEFAULT_SETTINGS.copy()
            self._save_settings()
        else:
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge deep defaults (simple implementation)
                    # For production, utilize a deep merge utility
                    self.settings = {**DEFAULT_SETTINGS, **data}
                    
                    # Ensure sub-dicts exist (shallow merge fix)
                    for key, val in DEFAULT_SETTINGS.items():
                        if key not in self.settings:
                             self.settings[key] = val
                        elif isinstance(val, dict):
                             self.settings[key] = {**val, **self.settings.get(key, {})}
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                self.settings = DEFAULT_SETTINGS.copy()

    def _save_settings(self):
        """Persists settings to JSON."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_all(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """Returns all settings, optionally masking API keys."""
        data = self.settings.copy()
        if mask_secrets:
            # Deep copy to avoid modifying memory state
            import copy
            safe_data = copy.deepcopy(data)
            ints = safe_data.get("integrations", {})
            for key in ["openai_api_key", "groq_api_key"]:
                if ints.get(key):
                    ints[key] = "sk-..." + ints[key][-4:]
            safe_data["integrations"] = ints
            return safe_data
        return data

    def update(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Updates settings. Expects partial updates."""
        # Recursive update or deep merge would be better, but we assume
        # frontend sends structured sections
        
        for section, content in new_settings.items():
            if section in self.settings and isinstance(content, dict):
                # Update existing section
                self.settings[section].update(content)
            else:
                # New section or overwrite
                self.settings[section] = content
        
        self._save_settings()
        return self.get_all(mask_secrets=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a specific setting (dot notation supported: 'system.language')."""
        if "." in key:
            section, subkey = key.split(".", 1)
            return self.settings.get(section, {}).get(subkey, default)
        return self.settings.get(key, default)

# Singleton instance
settings_manager = SettingsManager()
