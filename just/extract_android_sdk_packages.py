#!/usr/bin/env python3
"""Extract the list of Android SDK packages from android_sdk_manager.cpp.

Uses libclang to parse the C++ source and read the initializer list of the
global `ANDROID_SDK_PACKAGES` array (an array of `const char *`).

Usage:
    python extract_android_sdk_packages.py [path/to/android_sdk_manager.cpp]

The script prints each package on its own line, skipping the trailing `nullptr`
terminator used by the C++ array.
"""

import argparse
import os
import sys

from clang import cindex

# Name of the C++ global array we're interested in.
VARIABLE_NAME = "ANDROID_SDK_PACKAGES"

# Common locations for the libclang shared library on Windows/macOS/Linux.
LIBCLANG_CANDIDATE_PATHS = [
    os.environ.get("LIBCLANG_LIBRARY_PATH", ""),
    r"C:\dev\LLVM\bin",
    r"C:\Program Files\LLVM\bin",
    "/usr/lib/llvm/lib",
    "/usr/lib/llvm-*/lib",
    "/usr/local/opt/llvm/lib",
]


def configure_libclang():
    """Point the clang bindings at libclang if it isn't already resolvable."""
    if cindex.Config.library_path:
        return

    def is_usable(path):
        if not path:
            return False
        try:
            cindex.Config.set_library_path(path)
            cindex.Index.create()
            return True
        except Exception:
            return False

    for candidate in LIBCLANG_CANDIDATE_PATHS:
        if not candidate:
            continue
        if os.path.isfile(candidate):  # A file, e.g. libclang.dll / .so.
            try:
                cindex.Config.set_library_file(candidate)
                cindex.Index.create()
                return
            except Exception:
                continue
        if os.path.isdir(candidate) and is_usable(candidate):
            return

    # Fallback: try directories that contain a matching libclang file.
    for lib_name in ("libclang.dll", "libclang.so", "libclang.dylib"):
        for root in (r"C:\dev\LLVM", r"C:\Program Files\LLVM", "/usr"):
            for dirpath, _, filenames in os.walk(root):
                if lib_name in filenames and is_usable(dirpath):
                    return
                # Don't scan the whole filesystem.
                if dirpath.count(os.sep) - root.count(os.sep) > 3:
                    break


# Top-level directories (relative to the repo root) whose headers may be
# included by the source. Pointing libclang at these reduces cascading parse
# errors, although the array extraction works even if some includes fail.
INCLUDE_DIRS = [
    ".",
    "core",
    "editor",
    "scene",
    "modules",
    "platform",
]


def build_arguments(include_paths):
    """Build the clang command-line arguments used to parse the file."""
    args = ["-x", "c++", "-std=c++17"]
    # Tolerate unknown/missing headers and macros; we only need the AST for a
    # file-scope array initializer.
    args.append("-ferror-limit=0")
    for path in include_paths:
        if os.path.isdir(path):
            args.append("-isystem")
            args.append(path)
    return args


def find_variable(tu, name):
    """Walk the top-level cursors and return the one named `name`, if any."""
    for cursor in tu.cursor.get_children():
        if cursor.kind == cindex.CursorKind.VAR_DECL and cursor.spelling == name:
            return cursor
    return None


def string_literal_value(cursor):
    """Return the decoded C string value for a string-literal cursor."""
    # A StringLiteral cursor's spelling is the full literal including quotes
    # (e.g. `"platform-tools"`). Join any tokens that make it up and strip the
    # surrounding quotes.
    tokens = [t.spelling for t in cursor.get_tokens()]
    raw = "".join(tokens).strip()
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        # Unescape common C escapes so the output is the logical package path.
        body = raw[1:-1]
        return body.replace('\\"', '"').replace("\\\\", "\\")
    return raw


def extract_packages(source_path):
    """Parse `source_path` and return the list of Android SDK packages."""
    configure_libclang()
    index = cindex.Index.create()
    repo_root = os.path.dirname(os.path.abspath(__file__))
    include_paths = [os.path.join(repo_root, d) for d in INCLUDE_DIRS]
    args = build_arguments(include_paths)

    tu = index.parse(
        os.path.abspath(source_path),
        args=args,
        options=(
            cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES | cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        ),
    )

    var = find_variable(tu, VARIABLE_NAME)
    if var is None:
        raise RuntimeError("Could not find '{}' in '{}'.".format(VARIABLE_NAME, source_path))

    # The initializer is an InitListExpr; each child is one package (or the
    # `nullptr` terminator, which is a null-pointer expression).
    packages = []
    for element in var.get_children():
        if element.kind == cindex.CursorKind.INIT_LIST_EXPR:
            for item in element.get_children():
                # Only string literals are package names; the trailing
                # `nullptr` terminator is skipped naturally.
                if item.kind == cindex.CursorKind.STRING_LITERAL:
                    packages.append(string_literal_value(item))
            break

    return packages


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract the Android SDK packages from the ANDROID_SDK_PACKAGES "
            "array in android_sdk_manager.cpp using libclang."
        )
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="editor/export/android_sdk_manager.cpp",
        help="Path to android_sdk_manager.cpp (default: %(default)s).",
    )
    args = parser.parse_args()

    packages = extract_packages(args.source)
    print(" ".join(packages))


if __name__ == "__main__":
    sys.exit(main())
