import subprocess
import sys
import requests

def check_command_installed(command):
    """检查命令是否安装在系统中"""
    try:
        subprocess.run([command, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"{command} 已安装。")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"警告：未检测到 {command}。")

def check_python_version(min_version=(3, 8)):
    """检查Python版本是否符合要求"""
    if sys.version_info >= min_version:
        print(f"Python 版本符合要求：{sys.version.split()[0]}。")
    else:
        print(f"警告：Python 版本不符合要求，当前版本：{sys.version.split()[0]}，需要 >= {'.'.join(map(str, min_version))}。")

def check_api_response(url):
    """检查API接口是否可调用"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"API 接口调用成功：{url}。")
        else:
            print(f"警告：API 接口调用失败，状态码：{response.status_code}，接口：{url}。")
    except requests.RequestException as e:
        print(f"警告：无法连接到 API 接口：{url}，错误：{e}。")

if __name__ == "__main__":
    # 检查 ImageMagick 和 ffmpeg 是否安装
    check_command_installed('magick')  # ImageMagick 的命令通常是 `magick`
    check_command_installed('ffmpeg')

    # 检查 Python 版本
    check_python_version()

    # 检查 API 接口是否可调用，替换下面的 URL 为您要检查的实际接口
    check_api_response('https://example.com/api')
