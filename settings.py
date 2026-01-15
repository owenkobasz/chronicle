"""
Settings management for Chronicle photo organization tool.
Stores user preferences in a JSON configuration file.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


# Default settings file location (in user's home directory)
SETTINGS_FILE = Path.home() / ".chronicle_settings.json"


DEFAULT_SETTINGS = {
    "default_source": "",
    "default_destination": "",
    "default_move_files": False,
    "organization_scheme": "camera_year_month",  # Options: "camera_year_month", "year_month", "year_month_camera"
    "month_format": "full",  # Options: "full" (01 - January), "number" (01)
    "separate_file_types": True,  # Separate JPG/RAW/VIDEO into subfolders
}


def get_settings_file() -> Path:
    """Get the path to the settings file."""
    return SETTINGS_FILE


def load_settings() -> Dict[str, Any]:
    """
    Load settings from the settings file.
    Returns default settings if file doesn't exist or is invalid.
    """
    settings_file = get_settings_file()
    
    if not settings_file.exists():
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        # Merge with defaults to ensure all keys exist
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)
        return merged
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load settings file: {e}")
        print("Using default settings.")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to the settings file.
    Returns True if successful, False otherwise.
    """
    settings_file = get_settings_file()
    
    try:
        # Ensure parent directory exists
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return True
    except (IOError, OSError) as e:
        print(f"Error saving settings: {e}")
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a specific setting value.
    """
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """
    Set a specific setting value and save to file.
    """
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)


def get_default_source() -> Optional[str]:
    """Get the default source directory."""
    source = get_setting("default_source", "")
    return source if source else None


def get_default_destination() -> Optional[str]:
    """Get the default destination directory."""
    dest = get_setting("default_destination", "")
    return dest if dest else None


def get_default_move_files() -> bool:
    """Get the default move files preference."""
    return get_setting("default_move_files", False)


def set_default_source(path: str) -> bool:
    """Set the default source directory."""
    return set_setting("default_source", path)


def set_default_destination(path: str) -> bool:
    """Set the default destination directory."""
    return set_setting("default_destination", path)


def set_default_move_files(move: bool) -> bool:
    """Set the default move files preference."""
    return set_setting("default_move_files", move)


def reset_settings() -> bool:
    """Reset all settings to defaults."""
    return save_settings(DEFAULT_SETTINGS.copy())


def get_organization_scheme() -> str:
    """Get the organization scheme setting."""
    return get_setting("organization_scheme", "camera_year_month")


def get_month_format() -> str:
    """Get the month format setting."""
    return get_setting("month_format", "full")


def get_separate_file_types() -> bool:
    """Get the separate file types setting."""
    return get_setting("separate_file_types", True)


def set_organization_scheme(scheme: str) -> bool:
    """Set the organization scheme."""
    valid_schemes = ["camera_year_month", "year_month", "year_month_camera"]
    if scheme not in valid_schemes:
        raise ValueError(f"Invalid organization scheme. Must be one of: {valid_schemes}")
    return set_setting("organization_scheme", scheme)


def set_month_format(format_type: str) -> bool:
    """Set the month format."""
    valid_formats = ["full", "number"]
    if format_type not in valid_formats:
        raise ValueError(f"Invalid month format. Must be one of: {valid_formats}")
    return set_setting("month_format", format_type)


def set_separate_file_types(separate: bool) -> bool:
    """Set the separate file types setting."""
    return set_setting("separate_file_types", separate)
