@echo off
chcp 65001
if not exist ".venv" (
    echo 测试测试
) else (
    echo 测试测试测试
)

echo 激活虚拟环境...
call .venv\Scripts\activate


echo 安装依赖...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

echo 启动程序...
python main.py


echo 运行完成，按任意键退出。
pause > nul