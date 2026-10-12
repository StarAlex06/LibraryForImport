
import pandas as pd
import pytest

from table_importer import CsvSource
from table_importer.exceptions import (
    SourceNotFoundError,
    SheetNotFoundError,
)


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "people.csv"
    path.write_text(
        "name,age\n"
        "Alice,20\n"
        "Bob,25\n"
        "Charlie,\n"
        "Diana,30\n",
        encoding="utf-8",
    )
    return path


def test_list_sheets(csv_file):
    source = CsvSource(csv_file)

    assert source.list_sheets() == ["people.csv"]


def test_scan_limited_sample(csv_file):
    source = CsvSource(csv_file)

    metadata = source.scan("people.csv", sample_size=2)

    assert metadata.name == "people.csv"
    assert metadata.column_count == 2
    assert metadata.scanned_rows == 2
    assert metadata.row_count is None
    assert metadata.row_count_is_exact is False
    assert metadata.missing_counts_are_exact is False


def test_scan_entire_small_file(csv_file):
    source = CsvSource(csv_file)

    metadata = source.scan("people.csv", sample_size=100)

    assert metadata.row_count == 4
    assert metadata.row_count_is_exact is True
    assert metadata.missing_counts_are_exact is True

    age_column = next(
        column for column in metadata.columns
        if column.name == "age"
    )
    assert age_column.missing_count == 1
    assert age_column.scanned_count == 4


def test_read_chunk(csv_file):
    source = CsvSource(csv_file)

    chunk = source.read_chunk(
        sheet_name="people.csv",
        offset=1,
        chunk_size=2,
    )

    assert len(chunk) == 2
    assert chunk["name"].tolist() == ["Bob", "Charlie"]


def test_missing_file(tmp_path):
    source = CsvSource(tmp_path / "missing.csv")
    with pytest.raises(SourceNotFoundError):
        source.scan("missing.csv")


def test_invalid_sheet_name(csv_file):
    source = CsvSource(csv_file)

    with pytest.raises(SheetNotFoundError):
        source.scan("other.csv")


def test_invalid_chunk_arguments(csv_file):
    source = CsvSource(csv_file)

    with pytest.raises(ValueError):
        source.read_chunk("people.csv", offset=-1, chunk_size=2)

    with pytest.raises(ValueError):
        source.read_chunk("people.csv", offset=0, chunk_size=0)
