
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from table_importer.metadata import SheetMetadata


class DataSource(ABC):
    """Abstract interface for a tabular data source."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @abstractmethod
    def list_sheets(self) -> list[str]:
        """Return names of available sheets or tables."""
        raise NotImplementedError

    @abstractmethod
    def scan(
        self,
        sheet_name: str,
        sample_size: int = 1000,
    ) -> SheetMetadata:
        """Inspect a source and return metadata using a limited sample."""
        raise NotImplementedError

    @abstractmethod
    def read_chunk(
        self,
        sheet_name: str,
        offset: int,
        chunk_size: int,
    ) -> pd.DataFrame:
        """Read a chunk of rows starting at the given offset."""
        raise NotImplementedError

    def iter_chunks(
        self,
        sheet_name: str,
        chunk_size: int,
        offset: int = 0,
    ):
        """Iterate over data chunks using the existing read_chunk method."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        if offset < 0:
            raise ValueError("offset cannot be negative.")

        while True:
            chunk = self.read_chunk(
                sheet_name=sheet_name,
                offset=offset,
                chunk_size=chunk_size,
            )

            yield chunk

            if chunk.empty or len(chunk) < chunk_size:
                return

            offset += len(chunk)
