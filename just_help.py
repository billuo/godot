#!/usr/bin/env python3
"""Combined command line tool for common Godot developer tasks.

This tool merges the functionality of `version.py`'s main block and
`extract_android_sdk_packages.py`'s main function into a single command line
tool with one sub-command per concern:

Sub-commands:
    version                       Print the current Godot version string.
    extract-android-sdk-packages  Extract the Android SDK packages from
                                  android_sdk_manager.cpp using libclang.
"""

import argparse
import sys

import version as godot_version
from just import extract_android_sdk_packages

# Sub-command names exposed on the command line.
VERSION_CMD = "version"
EXTRACT_ANDROID_SDK_CMD = "extract-android-sdk-packages"


def cmd_version(_args):
    """Print the Godot version string (equivalent to `version.py`'s main block)."""
    if godot_version.status == "dev":
        print(f"{godot_version.major}.{godot_version.minor}.{godot_version.status}")
    else:
        print(f"{godot_version.major}.{godot_version.minor}.{godot_version.patch}.{godot_version.status}")
    return 0


def cmd_extract_android_sdk_packages(args):
    """Extract and print the Android SDK packages as a space-separated list."""
    packages = extract_android_sdk_packages.extract_packages(args.source)
    print(" ".join(packages))
    return 0


def build_parser():
    """Build and return the argument parser for the combined tool."""
    parser = argparse.ArgumentParser(
        description=(
            "Print the Godot version and extract the Android SDK packages "
            "from the ANDROID_SDK_PACKAGES array in android_sdk_manager.cpp."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    sub_version = subparsers.add_parser(VERSION_CMD, help="Print the current Godot version.")
    sub_version.set_defaults(func=cmd_version)

    sub_extract = subparsers.add_parser(
        EXTRACT_ANDROID_SDK_CMD,
        help=(
            "Extract the Android SDK packages from the ANDROID_SDK_PACKAGES "
            "array in android_sdk_manager.cpp using libclang."
        ),
    )
    sub_extract.add_argument(
        "source",
        nargs="?",
        default="editor/export/android_sdk_manager.cpp",
        help="Path to android_sdk_manager.cpp (default: %(default)s).",
    )
    sub_extract.set_defaults(func=cmd_extract_android_sdk_packages)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
