
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

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
