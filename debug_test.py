from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

file_path = 'test_files/simple.xlsx'
with open(file_path, 'rb') as f:
    files = {
        'file': ('simple.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        'sheet_name': (None, 'Sheet1'),
        'limit': (None, 10),
        'offset': (None, 0),
    }
    response = client.post('/preview-rows', files=files)
    print('Status:', response.status_code)
    print('Response:', response.json())

