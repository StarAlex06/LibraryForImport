import pandas as pd
import pytest

from table_importer import TableImporter
from table_importer.exceptions import (
    SheetNotFoundError,
    TypeConversionError,
)


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "people.csv"
    path.write_text(
        "name,age\nAlice,20\nBob,25\nCharlie,30\nDiana,35\nEve,40\n",
        encoding="utf-8",
    )
    return path


def test_scan_through_public_api(csv_file):
    importer = TableImporter()

    metadata = importer.scan(csv_file, sample_size=2)

    assert metadata.scanned_rows == 2
    assert metadata.column_count == 2


def test_import_all_rows(csv_file):
    importer = TableImporter()

    data = importer.import_data(csv_file, chunk_size=2)

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 5
    assert data["name"].tolist() == [
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Eve",
    ]


def test_import_with_type_conversion(csv_file):
    importer = TableImporter()

    data = importer.import_data(
        csv_file,
        chunk_size=2,
        dtype={"age": "Int64"},
    )

    assert str(data["age"].dtype) == "Int64"


def test_type_conversion_error(csv_file):
    importer = TableImporter()

    with pytest.raises(TypeConversionError):
        importer.import_data(
            csv_file,
            dtype={"age": "not_a_real_type"},
        )


def test_progress_callback(csv_file):
    importer = TableImporter()
    progress = []

    data = importer.import_data(
        csv_file,
        chunk_size=2,
        progress_callback=progress.append,
    )

    assert len(data) == 5
    assert progress == [2, 4, 5]


def test_invalid_chunk_size(csv_file):
    importer = TableImporter()

    with pytest.raises(ValueError):
        importer.import_data(csv_file, chunk_size=0)


def test_unknown_sheet(csv_file):
    importer = TableImporter()

    with pytest.raises(SheetNotFoundError):
        importer.scan(csv_file, sheet_name="unknown")
