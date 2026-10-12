
import sqlite3
from pathlib import Path

import pandas as pd

from table_importer.base import DataSource
from table_importer.exceptions import (
    DataImportError,
    ScanError,
    SheetNotFoundError,
    SourceNotFoundError,
)
from table_importer.metadata import ColumnMetadata, SheetMetadata


class SQLiteSource(DataSource):
    """Data source implementation for SQLite database files."""

    def _check_file(self) -> None:
        if not self.path.exists():
            raise SourceNotFoundError(
                f"Database file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise SourceNotFoundError(
                f"Path is not a file: {self.path}"
            )

    def _connect(self) -> sqlite3.Connection:
        """Open a connection to an existing database."""
        self._check_file()

        try:
            connection = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=ro",
                uri=True,
            )
            connection.execute("PRAGMA query_only = ON")
            return connection
        except sqlite3.Error as exc:
            raise ScanError(
                f"Could not connect to SQLite database {self.path}: {exc}"
            ) from exc

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Escape an SQL identifier such as a table or column name."""
        return '"' + identifier.replace('"', '""') + '"'

    def list_sheets(self) -> list[str]:
        """Return names of user tables in the database."""
        connection = self._connect()

        try:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()

            return [row[0] for row in rows]
        except sqlite3.Error as exc:
            raise ScanError(
                f"Could not list tables in {self.path}: {exc}"
            ) from exc
        finally:
            connection.close()

    def _check_sheet_name(self, sheet_name: str) -> None:
        if sheet_name not in self.list_sheets():
            raise SheetNotFoundError(
                f"SQLite database has no table named {sheet_name!r}."
            )

    def scan(
        self,
        sheet_name: str,
        sample_size: int = 1000,
    ) -> SheetMetadata:
        """Inspect a limited sample of rows in a SQLite table."""
        self._check_file()

        if sample_size < 1:
            raise ValueError("sample_size must be greater than zero.")

        self._check_sheet_name(sheet_name)
        connection = self._connect()

        try:
            table = self._quote_identifier(sheet_name)
            data = pd.read_sql_query(
                f"SELECT * FROM {table} LIMIT ?",
                connection,
                params=(sample_size + 1,),
            )
        except Exception as exc:
            raise ScanError(
                f"Could not scan SQLite table {sheet_name!r}: {exc}"
            ) from exc
        finally:
            connection.close()

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
        """Read a chunk of rows from a SQLite table."""
        self._check_file()

        if offset < 0:
            raise ValueError("offset cannot be negative.")

        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        self._check_sheet_name(sheet_name)
        connection = self._connect()

        try:
            table = self._quote_identifier(sheet_name)
            return pd.read_sql_query(
                f"SELECT * FROM {table} LIMIT ? OFFSET ?",
                connection,
                params=(chunk_size, offset),
            )
        except Exception as exc:
            raise DataImportError(
                f"Could not read SQLite table {sheet_name!r}: {exc}"
            ) from exc
        finally:
            connection.close()
