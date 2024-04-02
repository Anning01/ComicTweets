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

sd_url, file_path = "http://127.0.0.1:7860/sdapi/v1/txt2img", os.path.abspath("./image")


class Main:
    sd_url = sd_url

    async def draw_picture(self, obj_list, book_name):
        """
        :param obj_list:
        :return: 图片地址列表
        """
        picture_path_list = []
        for index, obj in enumerate(tqdm(obj_list, desc='生成图片中', bar_format='{l_bar}{bar}: {n_fmt}/{total_fmt}')):
            novel_dict = {
                # 高分辨率放大，true=启用，false=关闭
                "enable_hr": "false",
                # 重绘幅度 0.4
                "denoising_strength": 0,
                # 图片宽度
                "firstphase_width": 540,
                # 图片高度
                "firstphase_height": 960,
                # 图片高分辨率放大倍数
                "hr_scale": 2,
                # 高分辨率放大渲染器 R-ESRGAN 4x+ Anime6B
                "hr_upscaler": "string",
                # 高分辨率放大迭代次数
                "hr_second_pass_steps": 0,  # 10
                # 绘图渲染器
                "sampler_name": "DPM adaptive",
                # 绘图数量
                "batch_size": 1,
                # 绘图迭代次数
                "steps": 30,
                # 引导词关联性
                "cfg_scale": 7,
                # 面部修复，true=启用，false=关闭
                "restore_faces": "false",
                # 负面提示词
                "negative_prompt": obj["negative_prompt"],
                # 正面提示词
                "prompt": obj["prompt"],
            }
            try:
                # 生成图片任务
                # html = requests.post(self.sd_url, data=json.dumps(novel_dict))
                # 替换成异步协程
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.sd_url, json=novel_dict) as response:
                        html = await response.read()
            except Exception as e:
                print(e)
                raise ConnectionError("Stable Diffusion 连接失败，请查看ip+端口是否匹配，是否开启。")
            try:
                img_response = json.loads(html)
            except Exception as e:
                if str(e) == "Expecting value: line 2 column 1 (char 1)":
                    raise Exception(f"{self.sd_url} 返回数据异常，请查看是否开启，或者是否连接成功。")
                raise Exception(str(html))
            images = img_response.get("images", None)
            if not images:
                raise Exception(img_response.get("errors", "Stable Diffusion 返回数据异常，请查看ip+端口是否匹配，是否开启。"))
            image_bytes = base64.b64decode(images[0])
            image = Image.open(io.BytesIO(image_bytes))
            # 图片存放
            picture_name = str(index) + ".png"
            name = book_name.rsplit(".", 1)[0]
            path = os.path.join(file_path, name)
            if not os.path.isdir(path):
                os.mkdir(path)
            picture_path = os.path.join(path, picture_name)
            image.save(picture_path)
            picture_path_list.append(picture_path)
            print(f"-----------生成第{index}张图片-----------")
        return picture_path_list
    

if __name__ == '__main__':
    main = Main()
    with open("./1txt.json", "r", encoding="utf-8") as f:
        obj_list = json.load(f)
    asyncio.run(main.draw_picture(obj_list, "1txt"))