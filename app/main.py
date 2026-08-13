# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import json

from app.converter import (
    convert_excel_to_markdown,
    split_markdown_for_context,
    get_excel_metadata,
    get_sheet_rows
)

app = FastAPI(
    title="Excel to Markdown Converter",
    description="Upload Excel files, select sheets/columns/rows, and convert to Markdown.",
    version="3.0.0"
)

ALLOWED_EXTENSIONS = {"xlsx", "xls"}

def validate_file_extension(filename: str) -> bool:
    if not filename:
        return False
    return filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS

@app.post("/preview")
async def preview_excel(file: UploadFile = File(...)):
    """Get Excel structure (sheets + columns + row counts)."""
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty."
            )
        
        metadata = get_excel_metadata(contents)
        
        return {
            "filename": file.filename,
            "sheets": metadata,
            "total_sheets": len(metadata)
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )

@app.post("/preview-rows")
async def preview_rows(
    file: UploadFile = File(...),
    sheet_name: str = Form(...),
    limit: int = Form(100),
    offset: int = Form(0)
):
    """Get row data from a specific sheet for selection."""
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty."
            )
        
        rows_data = get_sheet_rows(contents, sheet_name, limit=limit, offset=offset)
        return rows_data
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading rows: {str(e)}"
        )

@app.post("/convert")
async def convert_excel(
    file: UploadFile = File(...),
    selection: Optional[str] = Form(None),
    rows: Optional[str] = Form(None),
    chunk_size: Optional[int] = Query(None)
):
    """Convert selected sheets/columns/rows to Markdown."""
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )

    # Parse selection
    sheet_selection = None
    if selection and selection.strip():
        try:
            sheet_selection = json.loads(selection)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid selection JSON: {str(e)}"
            )

    # Parse row selection
    row_selection = None
    if rows and rows.strip():
        try:
            row_selection = json.loads(rows)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rows JSON: {str(e)}"
            )

    # Convert
    try:
        markdown_content = convert_excel_to_markdown(
            contents,
            sheet_selection=sheet_selection,
            row_selection=row_selection
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected conversion error."
        )

    # Chunk if requested
    if chunk_size and chunk_size > 0:
        chunks = split_markdown_for_context(markdown_content, max_chars=chunk_size)
        return {
            "filename": file.filename,
            "chunked": True,
            "chunk_size": chunk_size,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
    
    return {
        "filename": file.filename,
        "chunked": False,
        "markdown": markdown_content
    }

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}