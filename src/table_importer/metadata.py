from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMetadata:
    name: str
    data_type: str
    missing_count: int | None
    scanned_count: int


@dataclass(frozen=True)
class SheetMetadata:
    name: str
    row_count: int | None
    column_count: int
    columns: tuple[ColumnMetadata, ...]
    scanned_rows: int
    row_count_is_exact: bool
    missing_counts_are_exact: bool
