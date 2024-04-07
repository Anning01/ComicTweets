#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/06 11:33
# @file:load_config.py
import json
import os
import yaml
from aiofiles import os as aio_os
import aiofiles
# 自用配置文件路径
local_config_path = "local_config.yaml"
# 公共配置文件路径
public_config_path = "config.yaml"

# 尝试打开自用配置文件
if os.path.exists(local_config_path):
    config_path = local_config_path
else:
    # 如果自用配置文件不存在，使用公共配置文件
    config_path = public_config_path


def get_yaml_config(config_path=config_path):
    """读取yaml配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


# 自用配置文件路径
local_stable_diffusion_path = "stable_diffusion.json"
# 公共配置文件路径
public_stable_diffusion_path = "local_stable_diffusion.json"


def get_sd_config(config_path=public_stable_diffusion_path):
    """读取stable diffusion配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


async def print_tip(tip, blank_line=0):
    """打印提示文字和空行"""
    blank = '\n' * blank_line if blank_line else ''
    print('-' * 20, tip, '-' * 20, blank)


async def check_file_exists(file_path):
    exists = await aio_os.path.exists(file_path)
    return exists


async def get_file(file_path):
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        content = await f.read()
    return content

