#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/06 17:20
# @file:async_main.py
import asyncio
import json
import os
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor

from aiofiles import os as aio_os
import aiofiles
from char2voice import create_voice_srt_new2
from check_path import check_command_installed, check_python_version
from extract_role import extract_potential_names
from load_config import get_yaml_config, print_tip, check_file_exists, get_file
from participle import participle
from prompt import generate_prompt
from sd import Main as sd
from video_composition import Main as vc

config = get_yaml_config()
name = config["book"]["name"]
memory = config["book"]["memory"]

if not name:
    raise Exception("请输入书名")
if not os.path.exists(f"{name}.txt"):
    raise Exception("请将小说文件放入根目录")


async def voice_srt(participle_path, path):
    await print_tip("开始生成语音字幕")
    async with aiofiles.open(participle_path, "r", encoding="utf8") as file:
        lines = await file.readlines()
        # 循环输出每一行内容
        index = 1
        for line in lines:
            if line:
                mp3_exists = await check_file_exists(os.path.join(path, f"{index}.mp3"))
                srt_exists = await check_file_exists(os.path.join(path, f"{index}.srt"))
                if memory and mp3_exists and srt_exists:
                    await print_tip(f"使用缓存，读取第{index}段语音字幕")
                else:
                    await create_voice_srt_new2(index, line, path)
                index += 1


async def role(path):
    await print_tip("开始提取角色")
    role_path = os.path.join(path, f"{name}.txt")
    print("提取角色")
    async with aiofiles.open(role_path, "r", encoding="utf8") as f:
        content = await f.read()
        novel_text = content.replace("\n", "").replace("\r", "").replace("\r\n", "")

    # 提取文本中的潜在人名
    names = await extract_potential_names(novel_text)
    await print_tip(f"查询出角色：{', '.join(names)}")
    text_ = ""
    for n in names:
        text_ += f"- {n}\n"

    async with aiofiles.open("prompt.txt", "r", encoding="utf8") as f:
        prompt_text = await f.read()

    async with aiofiles.open(f"{name}prompt.txt", "w", encoding="utf8") as f:
        await f.write(prompt_text + text_)
    # ToDo 做人物形象图


# async def draw_picture(path):
#     obj_path = os.path.join(path, f"{name}.json")
#     is_exists = await check_file_exists(obj_path)
#     while_count = 0
#     while not is_exists:
#         await print_tip("等待GPT生成提词器中，请稍等...")
#         await asyncio.sleep(6)
#         is_exists = await check_file_exists(obj_path)
#         while_count += 1
#         if while_count > 10:
#             raise Exception("GPT一分钟未生成提示词，请检查网络")
#     if while_count > 10:
#         raise Exception("GPT一分钟未生成提示词，请检查网络")
#
#     await print_tip("开始异步生成生成图片")
#
#     content = await get_file(obj_path)
#     obj_list = json.loads(content)
#     content_length = len(obj_list)
#     start_wait_time = datetime.now()
#     for index, obj in enumerate(obj_list, start=1):
#         await sd().draw_picture(obj, index, name)
#     while True:
#         content = await get_file(obj_path)
#
#         if content_length == len(json.loads(content)):
#             # 文件未变化
#             if datetime.now() - start_wait_time > timedelta(minutes=1):
#                 # 超过1分钟无变化
#                 await print_tip("已经将prompt全部执行完成，等待1分钟后未发现新的prompt，结束绘图。")
#                 break  # 退出循环
#             await asyncio.sleep(10)  # 短暂等待再次检查
#             continue
#         else:
#             content = await get_file(obj_path)
#             obj_list = json.loads(content)
#             for index, obj in enumerate(obj_list, start=1):
#                 await sd().draw_picture(obj, index, name)

async def new_draw_picture(path):
    obj_path = os.path.join(path, f"{name}.json")
    is_exists = await check_file_exists(obj_path)
    if not is_exists:
        raise Exception(f"{name}.json文件不存在")

    # content = await get_file(obj_path)
    # obj_list = json.loads(content)
    with open(obj_path, "r", encoding="utf-8") as f:
        obj_list = json.load(f)
    for index, obj in enumerate(obj_list, start=1):
        await print_tip(f"开始生成第{index}张图片")
        await sd().draw_picture(obj, index, name)


# 包装函数，用于在新进程中执行 voice_srt
def run_voice_srt_in_new_process(participle_path, path):
    # 在新进程中创建新的事件循环并运行 voice_srt
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(voice_srt(participle_path, path))
    loop.close()


async def main():
    await print_tip("正在分词")

    async with aiofiles.open(f"{name}.txt", "r", encoding="utf-8") as f:
        content = await f.read()
        novel = content.replace("\n", "").replace("\r", "").replace("\r\n", "").replace("\u2003", "")
    path = os.path.join("participle", name)
    await aio_os.makedirs(path, exist_ok=True)
    participle_path = os.path.join(path, f"{name}.txt")
    is_exists = await check_file_exists(participle_path)
    if memory and is_exists:
        await print_tip("读取缓存分词")
    else:
        async with aiofiles.open(participle_path, "w", encoding="utf-8") as f:
            participles = await participle(novel)
            await f.writelines(participles)
    await print_tip("分词完成")

    await role(path)

    # 创建 ProcessPoolExecutor 来运行新的进程
    executor = ProcessPoolExecutor()

    # 在新的进程中异步执行 voice_srt
    # 注意：这里不需要使用 run_coroutine_threadsafe
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(executor, run_voice_srt_in_new_process, participle_path, path)

    # await asyncio.gather(voice_srt(participle_path, path), generate_prompt(path, path, name), draw_picture(path))
    # await asyncio.gather(generate_prompt(path, path, name), draw_picture(path), future)
    await generate_prompt(path, path, name)
    await asyncio.gather(new_draw_picture(path), future)

    await print_tip("开始合成视频")
    picture_path_path = os.path.abspath(f"./images/{name}")
    audio_path_path = os.path.abspath(f"./participle/{name}")
    save_path = os.path.abspath(f"./video/{name}")
    vc().merge_video(picture_path_path, audio_path_path, name, save_path)


if __name__ == "__main__":
    # 检查 ImageMagick 和 ffmpeg 是否安装
    check_command_installed('magick')  # ImageMagick 的命令通常是 `magick`
    check_command_installed('ffmpeg')

    # 检查 Python 版本
    check_python_version()
    asyncio.run(main())
