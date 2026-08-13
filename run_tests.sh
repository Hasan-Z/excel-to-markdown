#!/bin/bash
# ============================================
#   Excel to Markdown - Test Runner
# ============================================

echo ""
echo "============================================"
echo "   Running All Tests"
echo "============================================"
echo ""

# Check if virtual environment exists
if [ ! -f "asr-env/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please create it first:"
    echo "  python -m venv asr-env"
    echo "  source asr-env/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Activate virtual environment
source asr-env/bin/activate

# Check if test files exist
if [ ! -f "test_files/simple.xlsx" ]; then
    echo "[INFO] Generating test files..."
    python generate_test_data.py
    echo ""
fi

# Run all tests
echo "[INFO] Running pytest..."
echo ""

pytest tests/ -v --tb=short

# Capture exit code
TEST_RESULT=$?

echo ""
echo "============================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "   ✅ All Tests Passed!"
else
    echo "   ❌ Some Tests Failed"
fi
echo "============================================"
echo ""

exit $TEST_RESULT