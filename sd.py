#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2023/08/01 14:30
# @file:app.py
import asyncio
import base64
import json
import os
import io
import aiofiles

import aiohttp
from PIL import Image
from tqdm import tqdm

from load_config import get_sd_config, get_yaml_config, check_file_exists, print_tip

config = get_yaml_config()
server_ip = config["stable_diffusion"]["server_ip"]
firstphase_width = config["stable_diffusion"]["width"]
firstphase_height = config["stable_diffusion"]["height"]
lora = config["stable_diffusion"]["lora"]
memory = config["book"]["memory"]

sd_url = server_ip + "/sdapi/v1/txt2img"


class Main:

    async def draw_picture(self, obj, index, save_path):
        data = get_sd_config()
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        is_exists = await check_file_exists(os.path.join(save_path, f"{index}.png"))
        if memory and is_exists:
            return
        prompt = obj["prompt"]
        if lora:
            prompt = f"{lora}, {prompt}"
        novel_dict = {
            "width": firstphase_width,
            "height": firstphase_height,
            "negative_prompt": obj["negative_prompt"],
            "prompt": prompt,
            **data,
        }
        try:
            # 替换成异步协程
            async with aiohttp.ClientSession() as session:
                async with session.post(sd_url, json=novel_dict) as response:
                    html = await response.read()
        except Exception as e:
            print(e)
            raise ConnectionError(
                "Stable Diffusion 连接失败，请查看ip+端口是否匹配，是否开启。"
            )
        try:
            img_response = json.loads(html)
        except Exception as e:
            if str(e) == "Expecting value: line 2 column 1 (char 1)":
                raise Exception(
                    f"{sd_url} 返回数据异常，请查看是否开启，或者是否连接成功。"
                )
            raise Exception(str(html))
        images = img_response.get("images", None)
        if not images:
            error = img_response.get(
                "error",
                "Stable Diffusion 返回数据异常，请查看ip+端口是否匹配，是否开启。",
            )
            raise Exception(error)
        image_bytes = base64.b64decode(images[0])
        image = Image.open(io.BytesIO(image_bytes))
        # 图片存放
        picture_name = str(index) + ".png"

        picture_path = os.path.join(save_path, picture_name)
        image.save(picture_path)


async def new_draw_picture(path, name, save_path):
    obj_path = os.path.join(path, f"{name}.json")
    is_exists = await check_file_exists(obj_path)
    if not is_exists:
        raise Exception(f"{name}.json文件不存在")

    with open(obj_path, "r", encoding="utf-8") as f:
        obj_list = json.load(f)
    for index, obj in enumerate(obj_list, start=1):
        await print_tip(f"开始生成第{index}张图片")
        await Main().draw_picture(obj, index, save_path)


if __name__ == "__main__":
    book_name = "千金"
    # main = Main()
    # with open("participle/千金/千金.json", "r", encoding="utf-8") as f:
    #     obj_list = json.load(f)
    # asyncio.run(main.draw_picture(obj_list, "千金"))
    file_path = os.path.join(book_name, "pictures")
    print(file_path)
