#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2023/08/01 18:08
# @file:app.py
import asyncio

import aiohttp
import requests
from aiohttp import ClientTimeout, ClientConnectionError
from requests import ConnectionError
from requests import Timeout

from load_config import get_yaml_config

config = get_yaml_config()
ForwardKey = config["chatgpt"]["ForwardKey"]

class Main:
    url = "https://oa.api2d.net/v1/chat/completions"

    def __str__(self):
        return "API2D请求失败，请检查配置！"

    async def fetch_data(self, headers, data):
        timeout = ClientTimeout(total=30)  # 设置总超时时间为15秒
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                response = await session.post(self.url, headers=headers, json=data)
                # 确保我们总是消费响应的内容，释放连接
                response_text = await response.text()
            except asyncio.TimeoutError:
                return False, "API2D连接超时，30秒未响应！"
            except ClientConnectionError:
                return False, f"连接错误，{self.url} 建立连接失败，请检查网络。"
            except Exception as e:
                return False, str(e)

            if response.status not in [200, 201]:  # 检查HTTP状态码
                try:
                    error_message = await response.json()
                except Exception:  # 如果响应不是JSON格式，则使用文本
                    error_message = response_text
                return False, error_message.get("message", "API2D返回状态码错误，请检查配置！")

            return True, response_text  # 或其他处理逻辑

    async def prompt_generation_chatgpt(self, param, messages):
        # 发送HTTP POST请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ForwardKey}",
        }

        msg = messages + [
            {
                "role": "user",
                "content": param,
            }
        ]
        data = {
            "model": "gpt-3.5-turbo",
            "messages": msg,
        }
        print("-----------开始请求API2D-----------")
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=15)
        except Timeout:
            return False, "API2D连接超时，15秒未响应！"
        except ConnectionError:
            return False, f"连接错误，{self.url} 建立连接失败，请检查网络。"
        except Exception as e:
            return False, str(e)
        if response.status_code != 200:
            return False, response.json().get(
                "message", "API2D返回状态码错误，请检查配置！"
            )
        # 发送HTTP POST请求
        result_json = response.json()
        # 输出结果
        # 计算token
        total_tokens = result_json["usage"]["total_tokens"]
        return msg, result_json["choices"][0]["message"], total_tokens


if __name__ == "__main__":

    with open("1txt.txt", "r", encoding="utf8") as file:
        # 初始化行数计数器
        line_number = 0
        lines = file.readlines()
        messages = []
        # 循环输出每一行内容
        for line in lines:
            line_number += 1

            text = f"第{line_number}段：" + line.strip()
            if line_number == 1:
                with open("prompt.txt", "r", encoding="utf8") as f:
                    messages = [
                        {
                            "role": "system",
                            "content": f.read(),
                        }
                    ]
            result, message = Main().prompt_generation_chatgpt(text, messages)

            messages = result + [message]
