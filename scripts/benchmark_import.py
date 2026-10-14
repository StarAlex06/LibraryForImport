
from __future__ import annotations

import argparse
import time
import tracemalloc
from pathlib import Path

from table_importer import TableImporter


FILE_NAMES = {
    "csv": "test_data.csv",
    "xlsx": "test_data.xlsx",
    "sqlite": "test_data.sqlite",
}


def benchmark_file(
    importer: TableImporter,
    path: Path,
    expected_rows: int,
    chunk_size: int,
) -> tuple[float, float, int]:
    """Return elapsed seconds, peak traced Python memory in MiB, and row count."""
    tracemalloc.start()
    start = time.perf_counter()

    try:
        result = importer.import_data(
            path,
            chunk_size=chunk_size,
        )
        elapsed = time.perf_counter() - start
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    actual_rows = len(result)
    peak_mib = peak_bytes / (1024 * 1024)

    if actual_rows != expected_rows:
        raise RuntimeError(
            f"{path.name}: expected {expected_rows} rows, "
            f"but imported {actual_rows}."
        )

    return elapsed, peak_mib, actual_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark TableImporter on generated test data."
    )
    parser.add_argument(
        "--rows",
        type=int,
        required=True,
        help="Expected number of rows in each generated file.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/generated"),
        help="Directory containing generated test files.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Number of rows per import chunk.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=("csv", "xlsx", "sqlite"),
        default=("csv", "xlsx", "sqlite"),
        help="Formats to benchmark.",
    )
    args = parser.parse_args()

    if args.rows < 0:
        parser.error("--rows must be non-negative")
    if args.chunk_size < 1:
        parser.error("--chunk-size must be positive")

    importer = TableImporter()
    failures = 0

    print(f"Expected rows: {args.rows:,}")
    print(f"Chunk size:    {args.chunk_size:,}")
    print()
    print(
        f"{'Format':<10} {'Seconds':>12} "
        f"{'Traced peak MiB':>18} {'Rows':>12}"
    )
    print("-" * 56)

    for format_name in args.formats:
        path = args.data_dir / FILE_NAMES[format_name]

        if not path.is_file():
            print(f"{format_name:<10} MISSING FILE: {path}")
            failures += 1
            continue

        try:
            elapsed, peak_mib, actual_rows = benchmark_file(
                importer=importer,
                path=path,
                expected_rows=args.rows,
                chunk_size=args.chunk_size,
            )
        except Exception as exc:
            print(f"{format_name:<10} FAILED: {exc}")
            failures += 1
            continue

        print(
            f"{format_name:<10} {elapsed:>12.2f} "
            f"{peak_mib:>18.2f} {actual_rows:>12,}"
        )

    print()
    if failures:
        raise SystemExit(f"Benchmark finished with {failures} failure(s).")

    print("All selected formats imported the expected number of rows.")


if __name__ == "__main__":
    main()
