# 📊 Excel to Markdown Converter

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-47%20tests-brightgreen.svg)]()

A powerful FastAPI web application that converts Excel files to Markdown tables with **selective sheet, column, and row filtering**. Perfect for preparing data for AI chatbots like ChatGPT, Claude, or any LLM.

![Features](https://img.shields.io/badge/features-sheets%20%7C%20columns%20%7C%20rows%20%7C%20chunking-blue)

---

## ✨ Features

- 📁 **Upload Excel Files** - Support for `.xlsx` and `.xls` formats
- 📋 **Selective Conversion** - Choose specific sheets, columns, and rows
- 🔍 **Live Preview** - See your data before converting
- ✂️ **Smart Chunking** - Each sheet gets its own chunk for better organization
- 📦 **Multiple Chunks** - Each chunk in its own textbox with copy button
- 📋 **Copy & Download** - Copy to clipboard or download as `.md` file
- 🎨 **Beautiful UI** - Modern, responsive design with drag & drop
- 🧪 **Full Test Coverage** - 47+ unit and integration tests
- 🔒 **JSON-Safe** - Handles NaN, inf, datetime, and special values

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/excel-to-md.git
cd excel-to-md
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv asr-env
asr-env\Scripts\activate

# macOS/Linux
python3 -m venv asr-env
source asr-env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Test Files (Optional)

```bash
python generate_test_data.py
```

### 5. Run the Application

```bash
# Using the batch file (Windows)
run-me.bat

# Or manually
uvicorn app.main:app --reload --port 8001
```

### 6. Open in Browser

```
http://127.0.0.1:8001
```

---

## 📖 Usage Guide

### Step 1: Upload Excel File

- Drag & drop your `.xlsx` or `.xls` file
- Or click to browse and select

### Step 2: Preview & Select

- **Sheets**: Check/uncheck entire sheets (click checkbox or sheet name)
  - ✅ Unchecked sheets are excluded from conversion
  - ✅ Visual feedback (grayed out when disabled)
- **Columns**: Select specific columns per sheet
  - ✅ Row preview updates to show only selected columns
- **Rows**: Enable "Select Specific Rows" to choose individual rows
  - Click "🔄 Load Rows" to preview
  - Check rows you want to include
  - Supports pagination for large files

### Step 3: Configure Chunking (Optional)

- Check "🔗 Split into chunks"
- Choose chunk size:
  - `3,500 chars` - Small chunks
  - `15,000 chars` - Medium (recommended)
  - `65,000 chars` - ChatGPT Web UI limit
  - `Custom` - Enter your own limit

**📋 Chunking Behavior:**
- ✅ **Each sheet ALWAYS gets its own chunk** (even if small)
- ✅ Large sheets are automatically split across multiple chunks
- ✅ Sheet headers always appear at the start of each chunk
- ✅ Perfect for copying one sheet at a time into AI chat

### Step 4: Convert & Export

- Click "🚀 Convert to Markdown"
- **Copy**: Copy individual chunks or all at once
- **Download**: Save as `.md` file
- **Back**: Return to selection to adjust

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger API documentation |
| `POST` | `/preview` | Get Excel structure (sheets + columns) |
| `POST` | `/preview-rows` | Get row data for selection |
| `POST` | `/convert` | Convert to Markdown |

### Example: Convert with Selection

```bash
curl -X POST "http://127.0.0.1:8001/convert?chunk_size=15000" \
  -F "file=@data.xlsx" \
  -F 'selection={"Sheet1": ["Name", "Score"]}' \
  -F 'rows={"Sheet1": [0, 1, 2]}'
```

### Example Response

```json
{
  "filename": "data.xlsx",
  "chunked": true,
  "chunk_size": 15000,
  "total_chunks": 3,
  "chunks": [
    "## Sheet1\n\n| Name | Score |\n|------|-------|\n| Alice | 95 |",
    "## Sheet2\n\n| Product | Price |\n|---------|-------|\n| Widget | 10 |",
    "## Sheet3\n\n| Date | Sales |\n|------|-------|\n| 2024 | 1000 |"
  ]
}
```

---

## 🧪 Running Tests

### Run All Tests

```bash
# Windows
run_tests.bat

# macOS/Linux
./run_tests.sh

# Or manually
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Converter logic tests
pytest tests/test_converter.py -v

# API endpoint tests
pytest tests/test_api.py -v

# Chunking tests
pytest tests/test_chunking.py -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=app --cov-report=html
```

---

## 📁 Project Structure

```
excel-to-md/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── converter.py         # Excel → Markdown logic
├── static/
│   └── index.html           # Web UI
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_converter.py    # Converter tests
│   ├── test_api.py          # API tests
│   └── test_chunking.py     # Chunking tests
├── test_files/              # Generated test Excel files
├── generate_test_data.py    # Test data generator
├── requirements.txt         # Python dependencies
├── run-me.bat               # Quick start (Windows)
├── run_tests.bat            # Test runner (Windows)
├── run_tests.sh             # Test runner (macOS/Linux)
└── README.md                # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8001` | Server port |
| `HOST` | `127.0.0.1` | Server host |
| `MAX_FILE_SIZE` | `10MB` | Maximum upload size |

### Chunk Size Recommendations

| Use Case | Chunk Size | Why |
|----------|------------|-----|
| GPT-3.5 Turbo | 3,500 chars | Fits within 4K token limit |
| GPT-4 Turbo | 15,000 chars | Comfortable for 128K context |
| ChatGPT Web UI | 65,000 chars | Maximum paste limit |
| Claude 3 | 30,000 chars | Works well with 200K context |
| Custom | Your choice | For specific model limits |

### Chunking Behavior

| Scenario | Behavior |
|----------|----------|
| **Small sheets** | Each sheet = 1 chunk (never combined) |
| **Large sheets** | Split across multiple chunks |
| **Sheet headers** | Always at start of chunk |
| **Table rows** | Never split mid-row when possible |

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:** Make sure you're in the project root directory:
```bash
cd D:\MyProjects\excel-to-md
uvicorn app.main:app --reload
```

### Issue: "Out of range float values are not JSON compliant"

**Solution:** Already fixed! The app now sanitizes NaN, inf, -inf values automatically.

### Issue: Row preview shows wrong columns

**Solution:** Select your columns first, then click "🔄 Load Rows". The preview respects column selection.

### Issue: Port already in use

**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8002
```

### Issue: Sheet deselection not working

**Solution:** You can click either:
- ✅ Directly on the checkbox
- ✅ On the sheet name/header
Both methods work!

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install black flake8 pytest-cov

# Format code
black app/ tests/

# Run linter
flake8 app/ tests/

# Run tests
pytest tests/ -v --cov=app
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pandas](https://pandas.pydata.org/) - Data processing
- [Tabulate](https://pypi.org/project/tabulate/) - Markdown tables
- [Pytest](https://docs.pytest.org/) - Testing framework

---

## 📬 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/excel-to-md/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/excel-to-md/discussions)
- 📧 **Email**: your.email@example.com

---

<div align="center">

**Made with ❤️ using FastAPI & Python**

[⬆ Back to Top](#-excel-to-markdown-converter)

</div>