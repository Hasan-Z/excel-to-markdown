import pandas as pd
import os
from datetime import datetime, timedelta

# Ensure test_files directory exists
os.makedirs('test_files', exist_ok=True)

def create_simple_excel():
    """Creates a basic single-sheet Excel file."""
    data = {
        'ID': [1, 2, 3, 4],
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'Score': [85.5, 90.0, 78.5, 92.0],
        'Passed': [True, True, False, True]
    }
    df = pd.DataFrame(data)
    df.to_excel('test_files/simple.xlsx', index=False)
    print("✓ Created test_files/simple.xlsx")

def create_multi_sheet_excel():
    """Creates an Excel file with multiple sheets."""
    with pd.ExcelWriter('test_files/multi_sheet.xlsx', engine='openpyxl') as writer:
        # Sheet 1
        df1 = pd.DataFrame({'Product': ['A', 'B'], 'Price': [10, 20]})
        df1.to_excel(writer, sheet_name='Inventory', index=False)
        
        # Sheet 2
        df2 = pd.DataFrame({'Employee': ['John', 'Jane'], 'Role': ['Dev', 'QA']})
        df2.to_excel(writer, sheet_name='Staff', index=False)
        
        # Sheet 3
        df3 = pd.DataFrame({'Region': ['North', 'South'], 'Sales': [1000, 1500]})
        df3.to_excel(writer, sheet_name='Sales', index=False)
    print("✓ Created test_files/multi_sheet.xlsx")

def create_edge_cases_excel():
    """Creates an Excel file with special characters, empty cells, and dates."""
    data = {
        'Description': ['Item "One"', 'Item <Two>', 'Item & Three', None, 'Normal Item'],
        'Date': [datetime.now(), datetime.now() - timedelta(days=1), None, '', 'Not a date'],
        'Value': [100, None, 0, '', 50.5555], # Mix of None, empty string, numbers
        'Markdown_Chars': ['| pipe |', '**bold**', '# hash', '`code`', '~tilde~']
    }
    df = pd.DataFrame(data)
    df.to_excel('test_files/edge_cases.xlsx', index=False)
    print("✓ Created test_files/edge_cases.xlsx")

if __name__ == "__main__":
    print("Generating test Excel files...")
    try:
        create_simple_excel()
        create_multi_sheet_excel()
        create_edge_cases_excel()
        print("\n✅ All test files generated successfully in 'test_files/' folder.")
    except Exception as e:
        print(f"\n❌ Error generating files: {e}")