import pandas as pd

from table_importer.base import DataSource
from table_importer.exceptions import (
    DataImportError,
    ScanError,
    SheetNotFoundError,
    SourceNotFoundError,
)
from table_importer.metadata import ColumnMetadata, SheetMetadata


class CsvSource(DataSource):
    """Data source implementation for CSV files."""

    def _check_file(self) -> None:
        if not self.path.exists():
            raise SourceNotFoundError(f"File does not exist: {self.path}")

        if not self.path.is_file():
            raise SourceNotFoundError(f"Path is not a file: {self.path}")

    def _check_sheet_name(self, sheet_name: str) -> None:
        if sheet_name not in self.list_sheets():
            raise SheetNotFoundError(f"CSV source has no sheet named {sheet_name!r}.")

    def list_sheets(self) -> list[str]:
        """Return the CSV filename as the only available sheet."""
        return [self.path.name]

    def scan(
        self,
        sheet_name: str,
        sample_size: int = 1000,
    ) -> SheetMetadata:
        """Inspect up to sample_size rows of a CSV file."""
        self._check_file()
        self._check_sheet_name(sheet_name)

        if sample_size < 1:
            raise ValueError("sample_size must be greater than zero.")

        try:
            data = pd.read_csv(self.path, nrows=sample_size + 1)
        except Exception as exc:
            raise ScanError(f"Could not scan CSV file {self.path}: {exc}") from exc

        scanned_data = data.iloc[:sample_size]
        scanned_rows = len(scanned_data)
        all_rows_scanned = len(data) <= sample_size

        columns = tuple(
            ColumnMetadata(
                name=str(column),
                data_type=str(scanned_data[column].dtype),
                missing_count=int(scanned_data[column].isna().sum()),
                scanned_count=scanned_rows,
            )
            for column in scanned_data.columns
        )

        return SheetMetadata(
            name=sheet_name,
            row_count=scanned_rows if all_rows_scanned else None,
            column_count=len(scanned_data.columns),
            columns=columns,
            scanned_rows=scanned_rows,
            row_count_is_exact=all_rows_scanned,
            missing_counts_are_exact=all_rows_scanned,
        )

    def read_chunk(
        self,
        sheet_name: str,
        offset: int,
        chunk_size: int,
    ) -> pd.DataFrame:
        """Read a chunk of rows, excluding the header from the offset."""
        self._check_file()
        self._check_sheet_name(sheet_name)

        if offset < 0:
            raise ValueError("offset cannot be negative.")

        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        try:
            return pd.read_csv(
                self.path,
                skiprows=range(1, offset + 1),
                nrows=chunk_size,
            )
        except Exception as exc:
            raise DataImportError(
                f"Could not read CSV file {self.path}: {exc}"
            ) from exc

    def iter_chunks(
        self,
        sheet_name: str,
        chunk_size: int,
        offset: int = 0,
    ):
        """Read CSV chunks using one persistent pandas reader."""
        self._check_file()
        self._check_sheet_name(sheet_name)

        if offset < 0:
            raise ValueError("offset cannot be negative.")

        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        try:
            reader = pd.read_csv(
                self.path,
                skiprows=range(1, offset + 1),
                chunksize=chunk_size,
            )

            yielded_any = False

            with reader:
                for chunk in reader:
                    yielded_any = True
                    yield chunk

            if not yielded_any:
                # Preserve the column names for an empty CSV.
                yield pd.read_csv(self.path, nrows=0)

        except Exception as exc:
            raise DataImportError(
                f"Could not stream CSV file {self.path}: {exc}"
            ) from exc
