@echo off
set CURRENT_DIR=%CD%
echo ***** Current directory: %CURRENT_DIR% *****
set PYTHONPATH=%CURRENT_DIR%

call .venv\Scripts\activate
rem set HF_ENDPOINT=https://hf-mirror.com
streamlit run .\app.py --browser.gatherUsageStats=False --server.enableCORS=True