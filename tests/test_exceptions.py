import pytest

from table_importer import(TableImporterError, SourceNotFoundError)
def test_custom_exception_inherits_base_exception():
    with pytest.raises(TableImporterError):
        raise SourceNotFoundError("File does not exis")
