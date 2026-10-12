import pytest

from table_importer import DataSource, SourceRegistry
from table_importer.exceptions import UnsupportedFormatError


class DummySource(DataSource):
    """Minimal source implementation for registry tests."""
    def list_sheets(self) -> list[str]:
        return ["data"]
    def scan(self, sheet_name: str, sample_size: int = 1000):
        raise NotImplementedError
    def read_chunk(self, sheet_name:str,offset:int, chunk_size:int):
        raise NotImplementedError
def test_register_and_find_source():
    registry = SourceRegistry()
    registry.register(["csv",".txt"], DummySource)
    assert registry.get_source_class("data.csv") is DummySource
    assert registry.get_source_class("data.txt") is DummySource
def test_extension_is_case_insensitive():
    registry = SourceRegistry()
    registry.register(["CSV"],DummySource)

    assert registry.get_source_class("DATA.CSV") is DummySource

def test_unsupported_extension():
    registry = SourceRegistry()
    with pytest.raises(UnsupportedFormatError):
        registry.get_source_class("data.unknown")
def test_duplicate_registration():
    registry = SourceRegistry()
    registry.register(["csv"],DummySource)

    with pytest.raises(ValueError):
        registry.register([".csv"],DummySource)