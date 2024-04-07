@echo off
echo 创建虚拟环境...
python -m venv .venv

echo 激活虚拟环境...
call .venv\Scripts\activate

echo 安装依赖...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

echo 启动程序...
python main.py

echo 运行完成，按任意键退出。
pause > nul
