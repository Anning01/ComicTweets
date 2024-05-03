#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/05/01 23:40
# @file:chatgpt.py

from openai import OpenAI

from load_config import get_yaml_config

config = get_yaml_config()
ForwardKey = config["chatgpt"]["ForwardKey"]
base_url = config["chatgpt"]["url"]
model = config["chatgpt"]["model"]


class Main:

    client = OpenAI(
        api_key=ForwardKey,
        base_url=base_url,
    )

    def chat(self, query, history):

        history += [{
            "role": "user",
            "content": query
        }]

        completion = self.client.chat.completions.create(
            model=model,
            messages=history,
        )

        result = completion.choices[0].message.content

        history += [{
            "role": "assistant",
            "content": result
        }]

        return history, result, completion.usage.total_tokens
