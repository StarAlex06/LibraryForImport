from table_importer import ColumnMetadata, SheetMetadata


def test_column_metadata():
    column = ColumnMetadata(
        name="age",
        data_type="Int64",
        missing_count=2,
        scanned_count=100
    )
    assert column.name == "age"
    assert column.data_type == "Int64"
    assert column.missing_count == 2
    assert column.scanned_count == 100
def test_sheet_metadata():
    column = ColumnMetadata(
        name="age",
        data_type="Int64",
        missing_count=2,
        scanned_count = 100
    )
    sheet = SheetMetadata(
        name="people",
        row_count=1000,
        column_count = 1,
        columns=(column,),
        scanned_rows=100,
        row_count_is_exact=True,
        missing_counts_are_exact=False
    )
    assert sheet.name == "people"
    assert sheet.row_count == 1000
    assert sheet.scanned_rows == 100
    assert sheet.columns[0].name == "age"
    assert sheet.missing_counts_are_exact is False