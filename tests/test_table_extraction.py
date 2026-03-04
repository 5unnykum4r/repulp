import csv
import io
from pathlib import Path

import pytest

from repulp.extractor import extract_tables_structured, parse_markdown_table


SIMPLE_TABLE = """| Name  | Age | City    |
| ----- | --- | ------- |
| Alice | 30  | London  |
| Bob   | 25  | Berlin  |"""

MULTI_TABLE_MD = """# Report

Some text here.

| Product | Price |
| ------- | ----- |
| Widget  | 10    |
| Gadget  | 20    |

More text.

| Month | Revenue |
| ----- | ------- |
| Jan   | 1000    |
| Feb   | 1500    |
"""


class TestParseMarkdownTable:
    def test_returns_list_of_dicts(self):
        rows = parse_markdown_table(SIMPLE_TABLE)
        assert len(rows) == 2
        assert rows[0] == {"Name": "Alice", "Age": "30", "City": "London"}
        assert rows[1] == {"Name": "Bob", "Age": "25", "City": "Berlin"}

    def test_empty_table(self):
        table = "| H1 | H2 |\n| -- | -- |"
        rows = parse_markdown_table(table)
        assert rows == []

    def test_single_column(self):
        table = "| Value |\n| ----- |\n| hello |"
        rows = parse_markdown_table(table)
        assert rows == [{"Value": "hello"}]

    def test_duplicate_headers_disambiguated(self):
        table = "| Score | Score | Score |\n| ----- | ----- | ----- |\n| 10 | 20 | 30 |"
        rows = parse_markdown_table(table)
        assert len(rows) == 1
        assert rows[0] == {"Score": "10", "Score_1": "20", "Score_2": "30"}


class TestExtractTablesStructured:
    def test_returns_list_of_dict_lists(self):
        tables = extract_tables_structured(MULTI_TABLE_MD, format="dict")
        assert len(tables) == 2
        assert tables[0][0]["Product"] == "Widget"
        assert tables[1][0]["Month"] == "Jan"

    def test_returns_csv_strings(self):
        tables = extract_tables_structured(MULTI_TABLE_MD, format="csv")
        assert len(tables) == 2
        reader = csv.reader(io.StringIO(tables[0]))
        rows = list(reader)
        assert rows[0] == ["Product", "Price"]
        assert rows[1] == ["Widget", "10"]

    def test_returns_markdown(self):
        tables = extract_tables_structured(MULTI_TABLE_MD, format="markdown")
        assert len(tables) == 2
        assert "Widget" in tables[0]
        assert "|" in tables[0]

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            extract_tables_structured(SIMPLE_TABLE, format="xml")


class TestExtractTablesDataFrame:
    def test_returns_dataframes(self):
        pd = pytest.importorskip("pandas")
        tables = extract_tables_structured(MULTI_TABLE_MD, format="dataframe")
        assert len(tables) == 2
        assert isinstance(tables[0], pd.DataFrame)
        assert list(tables[0].columns) == ["Product", "Price"]
        assert tables[0].iloc[0]["Product"] == "Widget"

    def test_dataframe_from_single_table(self):
        pd = pytest.importorskip("pandas")
        tables = extract_tables_structured(SIMPLE_TABLE, format="dataframe")
        assert len(tables) == 1
        df = tables[0]
        assert len(df) == 2
        assert df.iloc[1]["Name"] == "Bob"
