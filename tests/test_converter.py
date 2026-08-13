# tests/test_converter.py
import pytest
import os
from app.converter import (
    convert_excel_to_markdown,
    get_excel_metadata,
    get_sheet_rows,
    _sanitize_value,
)


class TestSanitizeValue:
    """Test JSON-safe value sanitization."""

    def test_sanitize_none(self):
        """Test None value."""
        assert _sanitize_value(None) is None

    def test_sanitize_nan(self):
        """Test NaN value."""
        import math

        assert _sanitize_value(float("nan")) is None

    def test_sanitize_inf(self):
        """Test infinity values."""
        assert _sanitize_value(float("inf")) == "inf"
        assert _sanitize_value(float("-inf")) == "-inf"

    def test_sanitize_normal_values(self):
        """Test normal values pass through."""
        assert _sanitize_value(42) == 42
        assert _sanitize_value(3.14) == 3.14  # ✅ Float stays float
        assert _sanitize_value("hello") == "hello"
        assert _sanitize_value(True) is True


class TestConvertExcelToMarkdown:
    """Test basic Excel to Markdown conversion."""

    def test_convert_simple_file(self, simple_excel_path):
        """Test converting a simple Excel file."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        result = convert_excel_to_markdown(content)

        assert "## Sheet1" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "|" in result

    def test_convert_multi_sheet_file(self, multi_sheet_excel_path):
        """Test converting a multi-sheet Excel file."""
        with open(multi_sheet_excel_path, "rb") as f:
            content = f.read()

        result = convert_excel_to_markdown(content)

        assert "## Inventory" in result
        assert "## Staff" in result
        assert "## Sales" in result

    def test_convert_with_sheet_selection(self, multi_sheet_excel_path):
        """Test converting only selected sheets."""
        with open(multi_sheet_excel_path, "rb") as f:
            content = f.read()

        selection = {"Staff": None}
        result = convert_excel_to_markdown(content, sheet_selection=selection)

        assert "## Staff" in result
        assert "## Inventory" not in result

    def test_convert_with_column_selection(self, simple_excel_path):
        """Test converting only selected columns."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        selection = {"Sheet1": ["Name", "Score"]}
        result = convert_excel_to_markdown(content, sheet_selection=selection)

        assert "Name" in result
        assert "Score" in result
        assert "ID" not in result

    def test_convert_with_row_selection(self, simple_excel_path):
        """Test converting only selected rows."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        rows = {"Sheet1": [0, 1]}
        result = convert_excel_to_markdown(content, row_selection=rows)

        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" not in result

    def test_convert_with_combined_selection(self, multi_sheet_excel_path):
        """Test converting with sheet, column, and row selection."""
        with open(multi_sheet_excel_path, "rb") as f:
            content = f.read()

        sheet_selection = {"Inventory": ["Product"]}
        row_selection = {"Inventory": [0]}

        result = convert_excel_to_markdown(
            content, sheet_selection=sheet_selection, row_selection=row_selection
        )

        assert "## Inventory" in result
        assert "Product" in result

    def test_convert_empty_selection(self, simple_excel_path):
        """Test converting with no sheets selected."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        result = convert_excel_to_markdown(content, sheet_selection={})

        assert "*_No data selected_*" in result

    def test_convert_invalid_file(self):
        """Test converting invalid file content."""
        with pytest.raises(ValueError):
            convert_excel_to_markdown(b"This is not an Excel file")

    def test_convert_with_special_values(self, edge_cases_excel_path):
        """Test converting file with NaN, inf, special characters."""
        with open(edge_cases_excel_path, "rb") as f:
            content = f.read()

        result = convert_excel_to_markdown(content)

        assert "## Sheet1" in result
        assert isinstance(result, str)


class TestGetExcelMetadata:
    """Test Excel metadata extraction."""

    def test_get_metadata_simple(self, simple_excel_path):
        """Test getting metadata from simple file."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        metadata = get_excel_metadata(content)

        assert "Sheet1" in metadata
        assert "columns" in metadata["Sheet1"]
        assert "row_count" in metadata["Sheet1"]
        assert metadata["Sheet1"]["row_count"] == 4

    def test_get_metadata_multi_sheet(self, multi_sheet_excel_path):
        """Test getting metadata from multi-sheet file."""
        with open(multi_sheet_excel_path, "rb") as f:
            content = f.read()

        metadata = get_excel_metadata(content)

        assert len(metadata) == 3
        assert "Inventory" in metadata
        assert "Staff" in metadata
        assert "Sales" in metadata

    def test_get_metadata_columns(self, simple_excel_path):
        """Test that columns are correctly extracted."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        metadata = get_excel_metadata(content)

        assert "ID" in metadata["Sheet1"]["columns"]
        assert "Name" in metadata["Sheet1"]["columns"]
        assert "Score" in metadata["Sheet1"]["columns"]


class TestGetSheetRows:
    """Test row data extraction for preview."""

    def test_get_sheet_rows_basic(self, simple_excel_path):
        """Test getting rows from a sheet."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        result = get_sheet_rows(content, "Sheet1", limit=10, offset=0)

        assert result["sheet_name"] == "Sheet1"
        assert result["total_rows"] == 4
        assert result["offset"] == 0
        assert result["limit"] == 10
        assert len(result["rows"]) == 4
        assert result["has_more"] == False

    def test_get_sheet_rows_pagination(self, simple_excel_path):
        """Test row pagination."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        result1 = get_sheet_rows(content, "Sheet1", limit=2, offset=0)
        assert len(result1["rows"]) == 2
        assert result1["has_more"] == True

        result2 = get_sheet_rows(content, "Sheet1", limit=2, offset=2)
        assert len(result2["rows"]) == 2
        assert result2["has_more"] == False

    def test_get_sheet_rows_invalid_sheet(self, simple_excel_path):
        """Test getting rows from non-existent sheet."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        with pytest.raises(ValueError):
            get_sheet_rows(content, "NonExistentSheet", limit=10, offset=0)

    def test_get_sheet_rows_data_structure(self, simple_excel_path):
        """Test row data structure."""
        with open(simple_excel_path, "rb") as f:
            content = f.read()

        result = get_sheet_rows(content, "Sheet1", limit=10, offset=0)

        assert len(result["rows"]) > 0
        row = result["rows"][0]
        assert "index" in row
        assert "data" in row
        assert isinstance(row["index"], int)
        assert isinstance(row["data"], dict)

    def test_get_sheet_rows_sanitized_values(self, edge_cases_excel_path):
        """Test that row values are JSON-safe."""
        import json

        with open(edge_cases_excel_path, "rb") as f:
            content = f.read()

        result = get_sheet_rows(content, "Sheet1", limit=10, offset=0)

        # Should be JSON-serializable without errors
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
