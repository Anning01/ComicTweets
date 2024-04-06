#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/06 11:33
# @file:load_config.py
import json
import os
import yaml

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
