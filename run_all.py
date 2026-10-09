"""Rebuild everything from scratch: python run_all.py"""
import subprocess
import sys

STEPS = [
    ["generate_data.py"],
    ["clean_data.py"],
    ["run_sql.py"],
    ["build_analysis.py"],
    ["-m", "pytest", "-q"],
]

for step in STEPS:
    print(f"\n>>> {' '.join(step)}")
    subprocess.run([sys.executable, *step], check=True)
