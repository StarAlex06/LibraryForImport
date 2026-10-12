
from collections.abc import Callable, Mapping
from pathlib import Path

import pandas as pd

from table_importer.csv_source import CsvSource
from table_importer.exceptions import (
    SheetNotFoundError,
    TypeConversionError,
)
from table_importer.metadata import SheetMetadata
from table_importer.registry import SourceRegistry


class TableImporter:
    """Public API for scanning and importing tabular data."""

    def __init__(self, registry: SourceRegistry | None = None) -> None:
        self.registry = registry or SourceRegistry()

        if registry is None:
            self.registry.register([".csv"], CsvSource)

    def _create_source(self, path: str | Path):
        source_class = self.registry.get_source_class(path)
        return source_class(path)

    @staticmethod
    def _resolve_sheet(
        source,
        sheet_name: str | None,
    ) -> str:
        sheets = source.list_sheets()

        if sheet_name is not None:
            if sheet_name not in sheets:
                raise SheetNotFoundError(
                    f"Source has no sheet or table named {sheet_name!r}."
                )
            return sheet_name

        if not sheets:
            raise SheetNotFoundError(
                "The source does not contain any sheets or tables."
            )

        return sheets[0]

    def scan(
        self,
        path: str | Path,
        sheet_name: str | None = None,
        sample_size: int = 1000,
    ) -> SheetMetadata:
        """Scan a source and return metadata."""
        source = self._create_source(path)
        selected_sheet = self._resolve_sheet(source, sheet_name)

        return source.scan(
            sheet_name=selected_sheet,
            sample_size=sample_size,
        )

    def import_data(
        self,
        path: str | Path,
        sheet_name: str | None = None,
        chunk_size: int = 10_000,
        dtype: Mapping[str, str] | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> pd.DataFrame:
        """Import a complete source into one pandas DataFrame."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        source = self._create_source(path)
        selected_sheet = self._resolve_sheet(source, sheet_name)

        chunks: list[pd.DataFrame] = []
        offset = 0

        while True:
            chunk = source.read_chunk(
                sheet_name=selected_sheet,
                offset=offset,
                chunk_size=chunk_size,
            )

            if dtype:
                try:
                    chunk = chunk.astype(dict(dtype))
                except (ValueError, TypeError, OverflowError) as exc:
                    raise TypeConversionError(
                        f"Could not convert column types: {exc}"
                    ) from exc

            if not chunk.empty:
                chunks.append(chunk)
                offset += len(chunk)

                if progress_callback is not None:
                    progress_callback(offset)

            if len(chunk) < chunk_size:
                break

        if not chunks:
            return pd.DataFrame()

        return pd.concat(chunks, ignore_index=True)
