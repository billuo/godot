import os
from pathlib import Path

CPU_COUNT = os.cpu_count() or 1
N_JOBS = max(1, CPU_COUNT - 2)
BINDIR = Path(__file__).parent.parent.joinpath("bin")
