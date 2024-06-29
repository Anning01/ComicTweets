import os
import subprocess
import sys
import urllib.request
import zipfile

import nltk
import requests
from load_config import get_yaml_config
config = get_yaml_config()
server_ip = config["stable_diffusion"]["server_ip"]


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


def download_and_install_nltk_data(package_name):
    try:
        # 检查包是否已经下载
        nltk.data.find(f'tokenizers/{package_name}')
        print(f"{package_name} 数据包已经安装。")
    except LookupError:
        # 如果没有安装，则下载并安装数据包
        print(f"{package_name} 数据包未安装，正在下载...")

        # 定义下载 URL 和目标路径
        url = f'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/{package_name}.zip'
        download_path = f'{package_name}.zip'

        # 下载文件
        urllib.request.urlretrieve(url, download_path)
        print(f"{package_name} 数据包下载完成。")

        # 找到NLTK数据目录
        nltk_data_dir = nltk.data.find('')
        extract_path = os.path.join(nltk_data_dir, 'tokenizers')

        # 如果tokenizers目录不存在，则创建它
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        # 解压文件到目标路径
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # 删除下载的 zip 文件
        os.remove(download_path)

        print(f"{package_name} 数据包已安装到 {extract_path}")


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

    # 检测SD
    check_api_response(server_ip)

    # punkt 为英语包 其他包替换
    download_and_install_nltk_data('punkt')