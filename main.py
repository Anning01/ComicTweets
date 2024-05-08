#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/06 17:20
# @file:async_main.py
import asyncio
import json
import os
import random
from concurrent.futures import ProcessPoolExecutor

import aiofiles

from check_path import check_command_installed, check_python_version
from extract_role import extract_potential_names
from load_config import get_yaml_config, print_tip
from participle import main as participle
from prompt import generate_prompt
from sd import new_draw_picture
from video_composition import Main as vc
from voice_caption import voice_srt

config = get_yaml_config()

memory = config["book"]["memory"]
once = config["video"]["once"]
is_translate = config["potential"]["translate"]
name = config["book"]["name"]
role_enabled = config["stable_diffusion"]["role"]

if not name:
    raise Exception("请输入书名")


async def role(path, book_name):
    await print_tip("开始提取角色")
    role_path = os.path.join(path, f"{book_name}.txt")
    async with aiofiles.open(role_path, "r", encoding="utf-8") as f:
        content = await f.read()
        novel_text = content.replace("\n", "").replace("\r", "").replace("\r\n", "")

    # 提取文本中的潜在人名
    names = await extract_potential_names(novel_text)
    await print_tip(f"查询出角色：{', '.join(names)}")
    if role_enabled:
        role_file = os.path.join(path, "role.json")
        if not os.path.exists(role_file):
            all_files = os.listdir("roles")
            images = [file for file in all_files if file.endswith('.png')]
            # 固定任务 抽卡
            data = []
            for i, n in enumerate(names):
                data.append({"name": n, "role": random.sample(images, len(names))[i]})

            async with aiofiles.open(role_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False))

    if not is_translate:
        async with aiofiles.open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_text = await f.read()
        text_ = ""
        for n in names:
            text_ += f"- {n}\n"
        async with aiofiles.open(f"{book_name}prompt.txt", "w", encoding="utf-8") as f:
            await f.write(prompt_text + text_)


# 包装函数，用于在新进程中执行 voice_srt
def run_voice_srt_in_new_process(participle_path, path, name):
    # 在新进程中创建新的事件循环并运行 voice_srt
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(voice_srt(participle_path, path, f'{name}.txt', name))
    loop.close()


async def main():
    if not os.path.exists(f"{name}.txt"):
        raise Exception("请将小说文件放入根目录")
    path = os.path.join(name, "participle")
    participle_path = os.path.join(path, f"{name}.txt")

    await participle(f"{name}.txt", path, participle_path)

    await role(path, name)

    # 创建 ProcessPoolExecutor 来运行新的进程
    executor = ProcessPoolExecutor()

    # 在新的进程中异步执行 voice_srt
    # 注意：这里不需要使用 run_coroutine_threadsafe
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(executor, run_voice_srt_in_new_process, participle_path, path, name)

    # await asyncio.gather(voice_srt(participle_path, path), generate_prompt(path, path, name), draw_picture(path))
    # await asyncio.gather(generate_prompt(path, path, name), draw_picture(path), future)
    await generate_prompt(path, path, name)
    save_path = os.path.join(name, "pictures")
    await asyncio.gather(new_draw_picture(path, name, save_path), future)
    # await asyncio.gather(new_draw_picture(path), voice_srt(participle_path, path))

    await print_tip("开始合成视频")
    picture_path_path = os.path.abspath(f"./{name}/pictures")
    audio_path_path = os.path.abspath(f"./{name}/participle")
    save_path = os.path.abspath(f"./{name}/video")
    vc().merge_video(picture_path_path, audio_path_path, name, save_path)


if __name__ == "__main__":
    # 检查 ImageMagick 和 ffmpeg 是否安装
    check_command_installed('magick')  # ImageMagick 的命令通常是 `magick`
    check_command_installed('ffmpeg')
    # 检查 Python 版本
    check_python_version()
    asyncio.run(main())
