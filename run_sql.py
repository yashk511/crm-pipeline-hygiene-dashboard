"""Execute the DuckDB business queries and export analysis marts.

Run from anywhere: paths are resolved relative to this file. Old marts are removed
first so a deleted query can never leave a stale CSV behind.
"""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"
OUTPUT_DIR = ROOT / "clean" / "sql_marts"


def run_queries() -> list[Path]:
    os.chdir(ROOT)  # the .sql files use repo-relative paths like clean/fact_opportunities.csv
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_DIR.glob("*.csv"):
        old.unlink()
    connection = duckdb.connect()
    outputs = []
    try:
        for sql_path in sorted(SQL_DIR.glob("*.sql")):
            result = connection.execute(sql_path.read_text(encoding="utf-8")).fetchdf()
            output_path = OUTPUT_DIR / f"{sql_path.stem}.csv"
            result.to_csv(output_path, index=False)
            outputs.append(output_path)
    finally:
        connection.close()
    return outputs


if __name__ == "__main__":
    for output in run_queries():
        print(output.relative_to(ROOT))
