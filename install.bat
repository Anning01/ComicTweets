@echo off
if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

python main.py

pause
