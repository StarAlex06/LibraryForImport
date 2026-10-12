
class TableImporterError(Exception):
    """Base exception for all table importer errors."""


class SourceNotFoundError(TableImporterError):
    """The specified data source does not exist."""


class UnsupportedFormatError(TableImporterError):
    """The data source format is not supported."""


class SheetNotFoundError(TableImporterError):
    """The requested sheet or table does not exist."""


class ScanError(TableImporterError):
    """An error occurred while scanning a data source."""


class DataImportError(TableImporterError):
    """An error occurred while importing data."""


class TypeConversionError(DataImportError):
    """A value could not be converted to the requested type."""


class ImportStateError(TableImporterError):
    """The import session is in an invalid state."""
