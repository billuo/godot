import os
import ast
from pathlib import Path


def get_version(version_file: Path) -> str:
    a = ast.parse(version_file.read_text())
    d = {}
    for e in ast.walk(a):
        if isinstance(e, ast.Assign):
            k = e.targets[0]
            v = e.value
            if isinstance(k, ast.Name) and isinstance(v, ast.Constant):
                d[k.id] = v.value
    major = d.get("major", 0)
    minor = d.get("minor", 0)
    patch = d.get("patch", 0)
    status = d.get("status", "stable")
    if patch == 0:
        return f"{major}.{minor}.{status}"
    else:
        return f"{major}.{minor}.{patch}.{status}"


CPU_COUNT = os.cpu_count() or 1
N_JOBS = max(1, CPU_COUNT - 2)
BINDIR = Path(__file__).parent.parent.joinpath("bin")
VERSION = get_version(Path(__file__).parent.parent.joinpath("version.py"))
