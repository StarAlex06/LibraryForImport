
import pytest

from table_importer import TableImporter
from table_importer.exceptions import ImportStateError


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "people.csv"
    path.write_text(
        "name,age\n"
        "Alice,20\n"
        "Bob,25\n"
        "Charlie,30\n"
        "Diana,35\n"
        "Eve,40\n",
        encoding="utf-8",
    )
    return path


def test_session_reads_chunks(csv_file):
    importer = TableImporter()
    session = importer.create_session(csv_file, chunk_size=2)

    first = session.read_next_chunk()
    second = session.read_next_chunk()

    assert len(first) == 2
    assert len(second) == 2
    assert session.offset == 4
    assert not session.is_finished


def test_session_pause_and_resume(csv_file):
    importer = TableImporter()
    session = importer.create_session(csv_file, chunk_size=2)

    session.read_next_chunk()
    session.pause()

    assert session.is_paused

    with pytest.raises(ImportStateError):
        session.read_next_chunk()

    session.resume()

    assert not session.is_paused

    next_chunk = session.read_next_chunk()
    assert next_chunk["name"].tolist() == ["Charlie", "Diana"]


def test_session_returns_all_imported_rows(csv_file):
    importer = TableImporter()
    session = importer.create_session(csv_file, chunk_size=2)

    session.read_next_chunk()
    session.pause()

    result = session.get_result()

    assert len(result) == 2
    assert result["name"].tolist() == ["Alice", "Bob"]


def test_session_finishes_after_last_partial_chunk(csv_file):
    importer = TableImporter()
    session = importer.create_session(csv_file, chunk_size=3)

    session.read_next_chunk()
    last_chunk = session.read_next_chunk()

    assert len(last_chunk) == 2
    assert session.is_finished
    assert len(session.get_result()) == 5


def test_session_rejects_read_after_finish(csv_file):
    importer = TableImporter()
    session = importer.create_session(csv_file, chunk_size=10)

    session.read_next_chunk()

    assert session.is_finished

    with pytest.raises(ImportStateError):
        session.read_next_chunk()


def test_session_type_conversion(csv_file):
    importer = TableImporter()
    session = importer.create_session(
        csv_file,
        chunk_size=2,
        dtype={"age": "Int64"},
    )

    session.read_next_chunk()
    result = session.get_result()

    assert str(result["age"].dtype) == "Int64"


def test_import_data_still_works(csv_file):
    importer = TableImporter()

    result = importer.import_data(csv_file, chunk_size=2)

    assert len(result) == 5
    assert result["name"].tolist() == [
        "Alice",
        "Bob",
        "Charlie",
        "Diana",
        "Eve",
    ]
