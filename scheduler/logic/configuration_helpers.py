from typing import Dict, Any

from scheduler.logic.file_paths import CONFIG_FILE
from scheduler.logic.json_help_functions import _load_json, _save_json_with_lock



def load_config() -> Dict[str, Any]:
    """
    Reads 'config.json' and return dict.
    """

    return _load_json(CONFIG_FILE)


def save_config(config: Dict[str, Any]) -> None:
    """
    Saves 'config.json' safely.
    """

    _save_json_with_lock(CONFIG_FILE, config)

