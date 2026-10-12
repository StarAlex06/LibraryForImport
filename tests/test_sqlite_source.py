
import sqlite3

import pytest

from table_importer import SQLiteSource, TableImporter
from table_importer.exceptions import (
    SheetNotFoundError,
    SourceNotFoundError,
)


@pytest.fixture
def sqlite_file(tmp_path):
    path = tmp_path / "people.db"

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE people (
                name TEXT,
                age INTEGER
            )
            """
        )
        connection.executemany(
            "INSERT INTO people (name, age) VALUES (?, ?)",
            [
                ("Alice", 20),
                ("Bob", 25),
                ("Charlie", 30),
                ("Diana", 35),
                ("Eve", 40),
            ],
        )

        connection.execute(
            """
            CREATE TABLE cities (
                city TEXT
            )
            """
        )
        connection.executemany(
            "INSERT INTO cities (city) VALUES (?)",
            [("Moscow",), ("Berlin",)],
        )

    return path


def test_list_tables(sqlite_file):
    source = SQLiteSource(sqlite_file)

    assert source.list_sheets() == ["cities", "people"]


def test_scan_table(sqlite_file):
    source = SQLiteSource(sqlite_file)

    metadata = source.scan("people", sample_size=2)

    assert metadata.name == "people"
    assert metadata.column_count == 2
    assert metadata.scanned_rows == 2
    assert metadata.row_count is None
    assert not metadata.row_count_is_exact
    assert [column.name for column in metadata.columns] == [
        "name",
        "age",
    ]


def test_scan_small_table_exactly(sqlite_file):
    source = SQLiteSource(sqlite_file)

    metadata = source.scan("cities", sample_size=10)

    assert metadata.row_count == 2
    assert metadata.row_count_is_exact


def test_read_chunk(sqlite_file):
    source = SQLiteSource(sqlite_file)

    chunk = source.read_chunk(
        sheet_name="people",
        offset=2,
        chunk_size=2,
    )

    assert chunk["name"].tolist() == ["Charlie", "Diana"]


def test_missing_file_raises_error(tmp_path):
    source = SQLiteSource(tmp_path / "missing.db")

    with pytest.raises(SourceNotFoundError):
        source.list_sheets()


def test_missing_table_raises_error(sqlite_file):
    source = SQLiteSource(sqlite_file)

    with pytest.raises(SheetNotFoundError):
        source.scan("unknown")


def test_api_imports_sqlite(sqlite_file):
    importer = TableImporter()

    result = importer.import_data(
        sqlite_file,
        sheet_name="people",
        chunk_size=2,
    )

    assert result["name"].tolist() == [
        "Alice", "Bob", "Charlie", "Diana", "Eve"
    ]
