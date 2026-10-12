
import pandas as pd
import pytest

from table_importer import ExcelSource, TableImporter
from table_importer.exceptions import (
    SheetNotFoundError,
    SourceNotFoundError,
)


@pytest.fixture
def excel_file(tmp_path):
    path = tmp_path / "people.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [20, 25, 30, 35, 40],
            }
        ).to_excel(writer, sheet_name="People", index=False)

        pd.DataFrame(
            {"city": ["Moscow", "Berlin"]}
        ).to_excel(writer, sheet_name="Cities", index=False)

    return path


def test_list_sheets(excel_file):
    source = ExcelSource(excel_file)

    assert source.list_sheets() == ["People", "Cities"]


def test_scan_excel_sheet(excel_file):
    source = ExcelSource(excel_file)

    metadata = source.scan("People", sample_size=2)

    assert metadata.name == "People"
    assert metadata.column_count == 2
    assert metadata.scanned_rows == 2
    assert metadata.row_count is None
    assert not metadata.row_count_is_exact
    assert [column.name for column in metadata.columns] == ["name", "age"]


def test_scan_small_sheet_exactly(excel_file):
    source = ExcelSource(excel_file)

    metadata = source.scan("Cities", sample_size=10)

    assert metadata.row_count == 2
    assert metadata.row_count_is_exact


def test_read_chunk(excel_file):
    source = ExcelSource(excel_file)

    chunk = source.read_chunk(
        sheet_name="People",
        offset=2,
        chunk_size=2,
    )

    assert chunk["name"].tolist() == ["Charlie", "Diana"]


def test_missing_file_raises_error(tmp_path):
    source = ExcelSource(tmp_path / "missing.xlsx")

    with pytest.raises(SourceNotFoundError):
        source.list_sheets()


def test_missing_sheet_raises_error(excel_file):
    source = ExcelSource(excel_file)

    with pytest.raises(SheetNotFoundError):
        source.scan("Unknown")


def test_api_imports_excel(excel_file):
    importer = TableImporter()

    result = importer.import_data(
        excel_file,
        sheet_name="People",
        chunk_size=2,
    )

    assert result["name"].tolist() == [
        "Alice", "Bob", "Charlie", "Diana", "Eve"
    ]

def test_scan_empty_excel_sheet(tmp_path):
    path = tmp_path / "empty.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(columns=["name", "age"]).to_excel(
            writer,
            sheet_name="People",
            index=False,
        )

    source = ExcelSource(path)
    metadata = source.scan("People", sample_size=10)

    assert metadata.row_count == 0
    assert metadata.row_count_is_exact
    assert metadata.column_count == 2
    assert [column.name for column in metadata.columns] == [
        "name", "age"
    ]


def test_import_empty_excel_sheet_preserves_columns(tmp_path):
    path = tmp_path / "empty.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(columns=["name", "age"]).to_excel(
            writer,
            sheet_name="People",
            index=False,
        )

    importer = TableImporter()
    result = importer.import_data(path, sheet_name="People")

    assert result.empty
    assert result.columns.tolist() == ["name", "age"]
