# tests/conftest.py
import pytest
import os


@pytest.fixture
def test_files_dir():
    """Get path to test files directory."""
    return os.path.join(os.path.dirname(__file__), "..", "test_files")


@pytest.fixture
def simple_excel_path(test_files_dir):
    """Path to simple test Excel file."""
    return os.path.join(test_files_dir, "simple.xlsx")


@pytest.fixture
def multi_sheet_excel_path(test_files_dir):
    """Path to multi-sheet test Excel file."""
    return os.path.join(test_files_dir, "multi_sheet.xlsx")


@pytest.fixture
def edge_cases_excel_path(test_files_dir):
    """Path to edge cases test Excel file."""
    return os.path.join(test_files_dir, "edge_cases.xlsx")


@pytest.fixture
def large_excel_path(test_files_dir):
    """Path to large test Excel file for row selection."""
    return os.path.join(test_files_dir, "large.xlsx")
