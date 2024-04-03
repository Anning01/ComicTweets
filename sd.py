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

import aiohttp
from PIL import Image
from tqdm import tqdm
import yaml

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)
server_ip = config["stable_diffusion"]["server_ip"]
firstphase_width = config["stable_diffusion"]["width"]
firstphase_height = config["stable_diffusion"]["height"]
memory = config['book']['memory']

sd_url, file_path = server_ip + "/sdapi/v1/txt2img", os.path.abspath("./images")


class Main:

    async def draw_picture(self, obj_list, book_name):
        """
        :param obj_list:
        :return: 图片地址列表
        """
        with open("stable_diffusion.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        path = os.path.join(file_path, book_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        for index, obj in enumerate(
            tqdm(
                obj_list,
                desc="生成图片中",
                bar_format="{l_bar}{bar}: {n_fmt}/{total_fmt}",
            )
        ):
            if memory and os.path.exists(os.path.join(path, f"{index}.png")):
                continue
            novel_dict = {
                "firstphase_width": firstphase_width,
                "firstphase_height": firstphase_height,
                "negative_prompt": obj["negative_prompt"],
                "prompt": obj["prompt"],
                **data,
            }
            try:
                # 生成图片任务
                # html = requests.post(self.sd_url, data=json.dumps(novel_dict))
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
                raise Exception(
                    img_response.get(
                        "errors",
                        "Stable Diffusion 返回数据异常，请查看ip+端口是否匹配，是否开启。",
                    )
                )
            image_bytes = base64.b64decode(images[0])
            image = Image.open(io.BytesIO(image_bytes))
            # 图片存放
            picture_name = str(index) + ".png"
            
            picture_path = os.path.join(path, picture_name)
            image.save(picture_path)


if __name__ == "__main__":
    main = Main()
    with open("participle/千金/千金.json", "r", encoding="utf-8") as f:
        obj_list = json.load(f)
    asyncio.run(main.draw_picture(obj_list, "千金"))
