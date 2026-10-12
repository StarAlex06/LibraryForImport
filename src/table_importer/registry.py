
from pathlib import Path

from table_importer.base import DataSource
from table_importer.exceptions import UnsupportedFormatError


class SourceRegistry:
    """Registry of data source implementations."""

    def __init__(self) -> None:
        self._sources: dict[str, type[DataSource]] = {}

    def register(
        self,
        extensions: list[str],
        source_class: type[DataSource],
    ) -> None:
        """Register a source class for one or more file extensions."""
        for extension in extensions:
            normalized = self._normalize_extension(extension)

            if normalized in self._sources:
                raise ValueError(
                    f"Extension {normalized!r} is already registered."
                )

            self._sources[normalized] = source_class

    def get_source_class(self, path: str | Path) -> type[DataSource]:
        """Find a source implementation by file extension."""
        extension = Path(path).suffix.lower()

        if extension not in self._sources:
            raise UnsupportedFormatError(
                f"Unsupported file extension: {extension or '<none>'}"
            )

        return self._sources[extension]

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        normalized = extension.strip().lower()

        if not normalized:
            raise ValueError("Extension cannot be empty.")

        if not normalized.startswith("."):
            normalized = f".{normalized}"

        return normalized
