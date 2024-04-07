@echo off
REM 检查虚拟环境是否存在
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
)

REM 激活虚拟环境
echo Activating virtual environment...
call .venv\Scripts\activate

REM 安装依赖
echo Installing dependencies from requirements.txt...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

REM 运行主脚本
echo Running main.py...
python main.py


