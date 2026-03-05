import json
import os

class Translations:
    _instance = None
    _translations = {}
    _current_language = "tr"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_language(cls._current_language)
        return cls._instance

    def _load_language(self, lang: str):
        path = os.path.join(os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "languages", f"{lang}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)

    def set_language(self, lang: str):
        self._current_language = lang
        self._load_language(lang)

    def get(self, key: str, default: str = "") -> str:
        keys = key.split(".")
        value = self._translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                return default or key
        return value if value is not None else (default or key)

    def get_current_language(self) -> str:
        return self._current_language

def t(key: str, default: str = "") -> str:
    return Translations().get(key, default)