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

        pd.DataFrame({"city": ["Moscow", "Berlin"]}).to_excel(
            writer, sheet_name="Cities", index=False
        )

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

    assert result["name"].tolist() == ["Alice", "Bob", "Charlie", "Diana", "Eve"]


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
    assert [column.name for column in metadata.columns] == ["name", "age"]


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


def test_iter_chunks_reads_all_rows_in_order(tmp_path):
    import pandas as pd

    from table_importer.excel_source import ExcelSource

    path = tmp_path / "stream.xlsx"
    pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["a", "b", "c", "d", "e"],
        }
    ).to_excel(path, index=False, sheet_name="Data")

    source = ExcelSource(path)
    chunks = list(source.iter_chunks("Data", chunk_size=2))

    assert [len(chunk) for chunk in chunks] == [2, 2, 1]

    result = pd.concat(chunks, ignore_index=True)
    assert result["id"].tolist() == [1, 2, 3, 4, 5]
    assert result["name"].tolist() == ["a", "b", "c", "d", "e"]


def test_iter_chunks_respects_initial_offset(tmp_path):
    import pandas as pd

    from table_importer.excel_source import ExcelSource

    path = tmp_path / "offset.xlsx"
    pd.DataFrame({"id": [10, 20, 30, 40, 50]}).to_excel(
        path, index=False, sheet_name="Data"
    )

    source = ExcelSource(path)
    chunks = list(source.iter_chunks("Data", chunk_size=2, offset=2))

    result = pd.concat(chunks, ignore_index=True)
    assert result["id"].tolist() == [30, 40, 50]


def test_iter_chunks_preserves_columns_for_empty_sheet(tmp_path):
    import pandas as pd

    from table_importer.excel_source import ExcelSource

    path = tmp_path / "empty.xlsx"
    pd.DataFrame(columns=["id", "name"]).to_excel(path, index=False, sheet_name="Data")

    source = ExcelSource(path)
    chunks = list(source.iter_chunks("Data", chunk_size=2))

    assert len(chunks) == 1
    assert chunks[0].empty
    assert list(chunks[0].columns) == ["id", "name"]


def test_iter_chunks_preserves_blank_rows_in_middle(tmp_path):
    import pandas as pd

    from table_importer.excel_source import ExcelSource

    path = tmp_path / "blank_row.xlsx"
    pd.DataFrame(
        {
            "id": [1, None, 3],
            "name": ["Alice", None, "Charlie"],
        }
    ).to_excel(path, index=False, sheet_name="Data")

    source = ExcelSource(path)
    chunks = list(source.iter_chunks("Data", chunk_size=2))

    result = pd.concat(chunks, ignore_index=True)

    assert len(result) == 3
    assert result["id"].iloc[0] == 1
    assert pd.isna(result["id"].iloc[1])
    assert result["id"].iloc[2] == 3
    assert result["name"].iloc[0] == "Alice"
    assert pd.isna(result["name"].iloc[1])
    assert result["name"].iloc[2] == "Charlie"
