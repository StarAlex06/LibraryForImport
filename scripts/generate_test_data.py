
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from openpyxl import Workbook
COLUMNS = ("id", "name", "category", "value", "active")
CATEGORIES = ("books", "electronics", "clothing", "food", "other")


def make_row(index: int) -> tuple[int, str, str, float, bool]:
    return (
        index,
        f"item_{index:08d}",
        CATEGORIES[index % len(CATEGORIES)],
        round((index % 100_000) / 100.0, 2),
        index % 2 == 0,
    )


def generate_csv(path: Path, rows: int) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMNS)

        for index in range(rows):
            writer.writerow(make_row(index))


def generate_xlsx(path: Path, rows: int) -> None:
    if rows + 1 > 1_048_576:
        raise ValueError(
            "Too many rows for a single Excel worksheet. "
            "Use at most 1,048,575 data rows."
        )

    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet("data")
    worksheet.append(COLUMNS)

    for index in range(rows):
        worksheet.append(make_row(index))

    workbook.save(path)


def generate_sqlite(path: Path, rows: int) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                value REAL NOT NULL,
                active INTEGER NOT NULL
            )
            """
        )

        batch_size = 10_000

        for start in range(0, rows, batch_size):
            end = min(start + batch_size, rows)
            batch = [
                make_row(index)
                for index in range(start, end)
            ]
            connection.executemany(
                """
                INSERT INTO items
                    (id, name, category, value, active)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (row_id, name, category, value, int(active))
                    for row_id, name, category, value, active in batch
                ],
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic CSV, XLSX and SQLite test data."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=100_000,
        help="Number of data rows to generate (default: 100000).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
        help="Directory for generated files.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=("csv", "xlsx", "sqlite"),
        default=("csv", "xlsx", "sqlite"),
        help="Formats to generate.",
    )
    args = parser.parse_args()

    if args.rows < 0:
        parser.error("--rows must be non-negative")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    generators = {
        "csv": (generate_csv, ".csv"),
        "xlsx": (generate_xlsx, ".xlsx"),
        "sqlite": (generate_sqlite, ".sqlite"),
    }

    for format_name in args.formats:
        generator, extension = generators[format_name]
        output_path = args.output_dir / f"test_data{extension}"
        if format_name == "sqlite" and output_path.exists():
            output_path.unlink()

        print(f"Generating {format_name.upper()}: {output_path}")
        generator(output_path, args.rows)
        print(f"Created {output_path}")


if __name__ == "__main__":
    main()
