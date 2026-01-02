#!/usr/bin/env python3
"""Decide how many worker threads a build should use.

The count is derived from the number of physical CPU cores, ignoring SMT
(hyper-threading) siblings, and scaled by a configurable load ratio:

    workers = max(1, floor(physical_cores * load_ratio))

Physical core detection is best effort and platform specific (Windows, Linux
and macOS). If it fails, the logical CPU count is used as a fallback, so the
result is never lower than one thread.

Usage:
    python worker_threads.py [load_ratio]
"""

import argparse
import ctypes
import math
import os
import re
import struct
import sys

# Share of the physical cores a build is allowed to use by default (2/3).
DEFAULT_LOAD_RATIO = 2 / 3

# Building with zero threads is impossible, so this is the lower bound.
MIN_WORKER_THREADS = 1


def parse_load_ratio(value):
    """Parse a load ratio given as a decimal, a fraction or a percentage.

    Accepts e.g. `0.5`, `2/3` or `66%`, and rejects anything outside the
    (0, 1] range with a `ValueError`.
    """
    text = value.strip()
    try:
        if text.endswith("%"):
            ratio = float(text[:-1]) / 100.0
        elif "/" in text:
            numerator, _, denominator = text.partition("/")
            ratio = float(numerator) / float(denominator)
        else:
            ratio = float(text)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"'{value}' is not a load ratio, e.g. 0.66, 2/3 or 66%.")

    if not 0 < ratio <= 1:
        raise ValueError(f"load ratio must be in the (0, 1] range, got '{value}'.")
    return ratio


def _windows_physical_core_count():
    """Count physical CPU cores on Windows via GetLogicalProcessorInformationEx."""
    from ctypes import wintypes

    relation_processor_core = 0
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_info = kernel32.GetLogicalProcessorInformationEx
    except (AttributeError, OSError):
        return None

    get_info.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
    get_info.restype = wintypes.BOOL

    # A first call with a null buffer reports the buffer size to allocate.
    size = wintypes.DWORD(0)
    get_info(relation_processor_core, None, ctypes.byref(size))
    if size.value == 0:
        return None

    buffer = ctypes.create_string_buffer(size.value)
    if not get_info(relation_processor_core, buffer, ctypes.byref(size)):
        return None

    # The buffer holds one SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX record per
    # physical core, each starting with its relationship and its size in bytes.
    data = buffer.raw[: size.value]
    cores = 0
    offset = 0
    while offset + 8 <= len(data):
        relationship, record_size = struct.unpack_from("<II", data, offset)
        if relationship == relation_processor_core:
            cores += 1
        if record_size < 8:
            break
        offset += record_size

    return cores or None


def _linux_physical_core_count():
    """Count physical CPU cores on Linux from the sysfs CPU topology."""
    topology_root = "/sys/devices/system/cpu"
    cores = set()
    try:
        cpu_dirs = os.listdir(topology_root)
    except OSError:
        return None

    for cpu_dir in cpu_dirs:
        if not re.fullmatch(r"cpu\d+", cpu_dir):
            continue
        topology = os.path.join(topology_root, cpu_dir, "topology")
        try:
            with open(os.path.join(topology, "physical_package_id")) as package_file:
                package_id = package_file.read().strip()
            with open(os.path.join(topology, "core_id")) as core_file:
                core_id = core_file.read().strip()
        except OSError:
            continue
        # SMT siblings share both the package and the core ID.
        cores.add((package_id, core_id))

    return len(cores) or None


def _macos_physical_core_count():
    """Count physical CPU cores on macOS via sysctlbyname("hw.physicalcpu")."""
    try:
        libc = ctypes.CDLL(None)
        sysctlbyname = libc.sysctlbyname
    except (AttributeError, OSError):
        return None

    sysctlbyname.argtypes = [
        ctypes.c_char_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_void_p,
        ctypes.c_size_t,
    ]
    count = ctypes.c_int(0)
    size = ctypes.c_size_t(ctypes.sizeof(count))
    if sysctlbyname(b"hw.physicalcpu", ctypes.byref(count), ctypes.byref(size), None, 0) != 0:
        return None

    return count.value or None


def physical_core_count():
    """Return the number of physical CPU cores, or `None` if it is unknown."""
    if sys.platform.startswith("linux"):
        detector = _linux_physical_core_count
    elif sys.platform == "darwin":
        detector = _macos_physical_core_count
    elif sys.platform == "win32":
        detector = _windows_physical_core_count
    else:
        return None

    return detector()


def worker_count(load_ratio=DEFAULT_LOAD_RATIO):
    """Return the number of worker threads a build should use."""
    cores = physical_core_count()
    if not cores:
        # Hyper-threading siblings overstate the real parallelism, but the
        # logical count still beats assuming a single core.
        cores = os.cpu_count()
    if not cores:
        return MIN_WORKER_THREADS

    return max(MIN_WORKER_THREADS, math.floor(cores * load_ratio))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Print the number of worker threads a build should use, that is floor(physical CPU "
            "cores * load ratio), with a minimum of 1. Hyper-threaded siblings are ignored."
        )
    )
    parser.add_argument(
        "load_ratio",
        nargs="?",
        type=parse_load_ratio,
        default="2/3",
        help=(
            "Share of the physical cores to use, as a decimal (0.5), fraction (2/3) or "
            "percentage (66%%), in the (0, 1] range (default: %(default)s)."
        ),
    )
    args = parser.parse_args()

    print(worker_count(args.load_ratio))


if __name__ == "__main__":
    sys.exit(main())
