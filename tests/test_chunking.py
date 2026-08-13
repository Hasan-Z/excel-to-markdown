# tests/test_chunking.py
import pytest
from app.converter import split_markdown_for_context


class TestSplitMarkdownForContext:
    """Test markdown chunking functionality."""

    def test_empty_input(self):
        """Test handling of empty input."""
        assert split_markdown_for_context("", max_chars=100) == []
        assert split_markdown_for_context(None, max_chars=100) == []

    def test_single_sheet_fits(self):
        """Test that a single sheet that fits returns as one chunk."""
        text = "## Sheet1\n\n| A | B |\n|---|---|\n| 1 | 2 |"
        result = split_markdown_for_context(text, max_chars=100)
        
        assert len(result) == 1
        assert result[0] == text

    def test_each_sheet_gets_own_chunk(self):
        """Test that each sheet ALWAYS gets its own chunk (even if small)."""
        text = "## Sheet1\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        text += "## Sheet2\n\n| X | Y |\n|---|---|\n| 3 | 4 |\n\n"
        text += "## Sheet3\n\n| P | Q |\n|---|---|\n| 5 | 6 |"
        
        # Even with large max_chars, each sheet should be separate
        result = split_markdown_for_context(text, max_chars=10000)
        
        assert len(result) == 3  # ✅ 3 sheets = 3 chunks
        assert result[0].startswith("## Sheet1")
        assert result[1].startswith("## Sheet2")
        assert result[2].startswith("## Sheet3")

    def test_large_sheet_split(self):
        """Test that large sheets are split by lines."""
        # Create a sheet with many rows
        text = "## Sheet1\n\n| Col | Data |\n|-----|--------|\n"
        text += "\n".join([f"| {i} | {'X' * 50} |" for i in range(100)])
        
        result = split_markdown_for_context(text, max_chars=500)
        
        assert len(result) > 1  # Should be split
        for chunk in result:
            assert len(chunk) <= 500

    def test_chunk_size_never_exceeded(self):
        """Verify no chunk ever exceeds max_chars."""
        text = "## Sheet1\n\n"
        text += "| Col | Data |\n|-----|--------|\n"
        text += "| " + "X" * 500 + " | Value |\n" * 50
        
        result = split_markdown_for_context(text, max_chars=500)
        
        for chunk in result:
            assert len(chunk) <= 500, f"Chunk exceeds max_chars: {len(chunk)} > 500"

    def test_sheet_header_at_chunk_start(self):
        """Test that sheet headers appear at the start of chunks."""
        text = "## Sheet1\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        text += "## Sheet2\n\n| X | Y |\n|---|---|\n| 3 | 4 |"
        
        result = split_markdown_for_context(text, max_chars=10000)
        
        # Each chunk should start with a sheet header
        for chunk in result:
            assert chunk.strip().startswith("##")

    def test_mixed_sheet_sizes(self):
        """Test chunking with mixed small and large sheets."""
        # Small sheet
        text = "## SmallSheet\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        # Large sheet (will be split)
        text += "## LargeSheet\n\n"
        text += "| Col | Data |\n|-----|--------|\n"
        text += "\n".join([f"| {i} | {'X' * 100} |" for i in range(50)])
        
        result = split_markdown_for_context(text, max_chars=1000)
        
        # First chunk should be the small sheet
        assert result[0].startswith("## SmallSheet")
        
        # Remaining chunks should be from the large sheet
        for chunk in result[1:]:
            assert len(chunk) <= 1000

    def test_single_row_per_chunk_boundary(self):
        """Test that rows aren't split mid-row when possible."""
        text = "## Sheet1\n\n"
        text += "| Name | Value | Description |\n"
        text += "|------|-------|-------------|\n"
        text += "| Item1 | 100 | This is a long description that might cause splitting |\n"
        text += "| Item2 | 200 | Another description |\n"
        
        result = split_markdown_for_context(text, max_chars=150)
        
        for chunk in result:
            assert len(chunk) <= 150

    def test_very_long_cell_content(self):
        """Test handling of very long cell content."""
        text = "## Sheet1\n\n"
        text += "| Col |\n|-----|\n"
        text += f"| {'A' * 2000} |\n"  # Very long cell
        
        result = split_markdown_for_context(text, max_chars=500)
        
        # Should handle long content by hard splitting
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 500

    def test_multiple_sheets_all_small(self):
        """Test that multiple small sheets each get their own chunk."""
        text = ""
        for i in range(5):
            text += f"## Sheet{i+1}\n\n"
            text += f"| ID | Name |\n|----|------|\n"
            text += f"| {i+1} | Test{i+1} |\n\n"
        
        # Even with very large max_chars, should get 5 chunks
        result = split_markdown_for_context(text, max_chars=50000)
        
        assert len(result) == 5  # ✅ 5 sheets = 5 chunks
        
        # Verify each chunk starts with correct sheet header
        for i, chunk in enumerate(result):
            assert f"## Sheet{i+1}" in chunk