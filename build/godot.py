import os
import sys
from enum import StrEnum
from pathlib import Path


class Platform(StrEnum):
    LINUX = "linuxbsd"
    MACOS = "macos"
    WINDOWS = "windows"
    WEB = "web"
    ANDROID = "android"


def get_current_platform() -> Platform:
    if (
        sys.platform.startswith("linux")
        or sys.platform.startswith("dragonfly")
        or sys.platform.startswith("freebsd")
        or sys.platform.startswith("netbsd")
        or sys.platform.startswith("openbsd")
    ):
        return Platform.LINUX
    elif sys.platform == "darwin":
        return Platform.MACOS
    elif sys.platform == "win32":
        return Platform.WINDOWS


# Godot standard data paths.
# See also: https://docs.godotengine.org/en/stable/tutorials/io/data_paths.html#editor-data-paths


def get_editor_data_path(platform: Platform = get_current_platform()) -> Path:
    match platform:
        case Platform.LINUX:
            return Path("~/.local/share/godot")
        case Platform.MACOS:
            return Path("~/Library/Application Support/Godot")
        case Platform.WINDOWS:
            return Path(os.environ["APPDATA"]) / "Godot"
    raise ValueError(f"Unsupported platform: {platform}")


def get_editor_setting_path(platform: Platform) -> Path:
    match platform:
        case Platform.LINUX:
            return Path("~/.config/godot")
        case Platform.MACOS:
            return Path("~/Library/Application Support/Godot")
        case Platform.WINDOWS:
            return Path(os.environ["APPDATA"]) / "Godot"
    raise ValueError(f"Unsupported platform: {platform}")


def get_cache_path(platform: Platform) -> Path:
    match platform:
        case Platform.LINUX:
            return Path("~/.cache/godot")
        case Platform.MACOS:
            return Path("~/Library/Caches/Godot")
        case Platform.WINDOWS:
            return Path(os.environ["TEMP"]) / "Godot"
    raise ValueError(f"Unsupported platform: {platform}")
