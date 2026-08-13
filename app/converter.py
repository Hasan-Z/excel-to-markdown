# app/converter.py
import pandas as pd
import io
import re
import math
from typing import Optional, Dict, List, Any


def _sanitize_value(value: Any) -> Any:
    """
    Convert values that can't be JSON-serialized to safe alternatives.
    """
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return str(value)
        return value

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (AttributeError, ValueError):
            return str(value)

    if hasattr(value, "item"):
        try:
            return value.item()
        except (AttributeError, ValueError):
            pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, (list, tuple)):
        return [_sanitize_value(v) for v in value]

    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}

    if isinstance(value, (str, int, bool, float)):
        return value

    return str(value)


def convert_excel_to_markdown(
    file_content: bytes,
    sheet_selection: Optional[Dict[str, List[str]]] = None,
    row_selection: Optional[Dict[str, List[int]]] = None,
) -> str:
    """
    Reads an Excel file and converts selected sheets/columns/rows to Markdown.
    """
    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_content), engine="openpyxl")
        markdown_output = []

        for sheet_name in excel_file.sheet_names:
            if sheet_selection is not None and sheet_name not in sheet_selection:
                continue

            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            if row_selection and sheet_name in row_selection:
                rows_to_include = row_selection[sheet_name]
                if rows_to_include:
                    valid_rows = [i for i in rows_to_include if 0 <= i < len(df)]
                    if valid_rows:
                        df = df.iloc[valid_rows].reset_index(drop=True)
                    else:
                        continue

            columns_to_include = (
                sheet_selection.get(sheet_name) if sheet_selection else None
            )
            if columns_to_include and columns_to_include:
                valid_cols = [c for c in columns_to_include if c in df.columns]
                if valid_cols:
                    df = df[valid_cols]
                else:
                    continue

            df = df.copy()
            for col in df.columns:
                df[col] = df[col].apply(_sanitize_value)

            df = df.fillna("")

            markdown_output.append(f"## {sheet_name}\n")

            if df.empty:
                markdown_output.append("*_Empty Sheet_*\n")
                continue

            table_md = df.to_markdown(index=False)
            markdown_output.append(table_md)
            markdown_output.append("\n")

        return "\n".join(markdown_output) if markdown_output else "*_No data selected_*"

    except Exception as e:
        raise ValueError(f"Failed to convert Excel file: {str(e)}")


def get_excel_metadata(file_content: bytes) -> Dict[str, Dict]:
    """Extract metadata from Excel file: sheets, columns, and row count."""
    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_content), engine="openpyxl")
        metadata = {}

        for sheet_name in excel_file.sheet_names:
            df_header = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1)
            df_full = pd.read_excel(excel_file, sheet_name=sheet_name)

            metadata[sheet_name] = {
                "columns": df_header.columns.tolist(),
                "row_count": len(df_full),
            }

        return metadata

    except Exception as e:
        raise ValueError(f"Failed to read Excel meta {str(e)}")


def get_sheet_rows(
    file_content: bytes, sheet_name: str, limit: int = 100, offset: int = 0
) -> Dict:
    """
    Get row data from a specific sheet for preview.
    All values are sanitized for JSON compatibility.
    """
    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_content), engine="openpyxl")

        if sheet_name not in excel_file.sheet_names:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        total_rows = len(df)

        paginated_df = df.iloc[offset : offset + limit]

        rows = []
        for idx, row in paginated_df.iterrows():
            row_data = {
                "index": int(idx),
                "data": {col: _sanitize_value(row[col]) for col in df.columns},
            }
            rows.append(row_data)

        return {
            "sheet_name": sheet_name,
            "total_rows": total_rows,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_rows,
            "rows": rows,
        }

    except Exception as e:
        raise ValueError(f"Failed to read sheet rows: {str(e)}")


def extract_table_header(table_text: str) -> str:
    """Extract the header rows from a markdown table."""
    lines = table_text.split("\n")
    header_lines = []

    for line in lines:
        if line.strip().startswith("|"):
            header_lines.append(line)
            if len(header_lines) == 2:
                break

    return "\n".join(header_lines)


def split_markdown_for_context(
    markdown_text: str, max_chars: int = 3500, repeat_headers: bool = True
) -> list[str]:
    """
    Splits Markdown output into chunks that fit within character limits.
    ✅ Each sheet ALWAYS starts on a new chunk (even if total < max_chars).
    ✅ Large sheets are split by lines while keeping table structure.
    """
    if not markdown_text:
        return []

    chunks = []
    
    # ✅ Split by sheet headers first (## SheetName)
    sections = re.split(r'(?=^##\s+.+$)', markdown_text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]
    
    for section in sections:
        # ✅ Each sheet starts on a new chunk (never combine sheets)
        
        # If sheet fits within limit, add as-is
        if len(section) <= max_chars:
            chunks.append(section.rstrip())
        else:
            # ✅ Sheet is too big, split it by lines
            lines = section.split("\n")
            temp_chunk = ""
            
            for line in lines:
                sep = "\n" if temp_chunk else ""
                if len(temp_chunk) + len(sep) + len(line) > max_chars:
                    if temp_chunk:
                        chunks.append(temp_chunk.rstrip())
                        temp_chunk = ""
                    
                    # Hard split long lines
                    if len(line) > max_chars:
                        for i in range(0, len(line), max_chars):
                            chunks.append(line[i : i + max_chars])
                    else:
                        temp_chunk = line
                else:
                    temp_chunk += sep + line
            
            if temp_chunk:
                chunks.append(temp_chunk.rstrip())

    # Final safety: ensure no chunk exceeds max_chars
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
        else:
            # Hard split by character count
            for i in range(0, len(chunk), max_chars):
                final_chunks.append(chunk[i : i + max_chars])

    return final_chunks