from collections.abc import Callable, Mapping

import pandas as pd

from table_importer.base import DataSource
from table_importer.exceptions import (
    ImportStateError,
    TypeConversionError,
)


class ImportSession:
    """A stateful, chunk-by-chunk import session."""

    def __init__(
        self,
        source: DataSource,
        sheet_name: str,
        chunk_size: int = 10_000,
        dtype: Mapping[str, str] | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        self.source = source
        self.sheet_name = sheet_name
        self.chunk_size = chunk_size
        self.dtype = dict(dtype) if dtype is not None else None
        self.progress_callback = progress_callback

        self.offset = 0
        self._chunks: list[pd.DataFrame] = []
        self._empty_frame: pd.DataFrame | None = None
        self._paused = False
        self._finished = False
        self._chunk_iterator = source.iter_chunks(
            sheet_name=sheet_name,
            chunk_size=chunk_size,
        )

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_finished(self) -> bool:
        return self._finished

    def pause(self) -> None:
        """Pause the session without discarding imported data."""
        if self._finished:
            raise ImportStateError("Cannot pause a finished import.")

        self._paused = True

    def resume(self) -> None:
        """Resume a paused session."""
        if self._finished:
            raise ImportStateError("Cannot resume a finished import.")

        self._paused = False

    def read_next_chunk(self) -> pd.DataFrame:
        """Read and store the next chunk."""
        if self._paused:
            raise ImportStateError("Import is paused. Call resume() before reading.")

        if self._finished:
            raise ImportStateError("Import is already finished.")

        try:
            chunk = next(self._chunk_iterator)
        except StopIteration:
            self._finished = True

            if self._empty_frame is None:
                self._empty_frame = pd.DataFrame()

            return self._empty_frame.iloc[:0].copy()

        if self._empty_frame is None:
            self._empty_frame = chunk.iloc[:0].copy()

        if chunk.empty:
            self._finished = True
            return chunk

        if self.dtype:
            try:
                chunk = chunk.astype(self.dtype)
            except (KeyError, ValueError, TypeError, OverflowError) as exc:
                raise TypeConversionError(
                    f"Could not convert column types: {exc}"
                ) from exc

        self._chunks.append(chunk)
        self.offset += len(chunk)

        if self.progress_callback is not None:
            self.progress_callback(self.offset)

        if len(chunk) < self.chunk_size:
            self._finished = True

        return chunk

    def get_result(self) -> pd.DataFrame:
        """Return all imported rows as a single DataFrame."""
        if self._chunks:
            return pd.concat(self._chunks, ignore_index=True)

        if self._empty_frame is not None:
            return self._empty_frame.copy()

        return pd.DataFrame()
