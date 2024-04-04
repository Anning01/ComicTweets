import json
import os

import yaml
from api2d import Main

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)
memory = config["book"]["memory"]


def write_to_json(data, filename):
    try:
        with open(filename, "rb+") as file:
            file.seek(0, 2)  # 移到文件末尾
            if file.tell():  # 如果文件非空
                file.seek(-1, 2)  # 定位到文件的最后一个字符（即结尾的 ']' 前）
                file.truncate()  # 删除最后一个字符（']'）
                if file.tell() > 1:
                    file.write(b",\n")  # 如果不是文件开头，写入逗号和换行符
                else:
                    file.write(b"\n")  # 否则只写入换行符
                file.write(json.dumps(data).encode())  # 写入新的 JSON 对象
                file.write(b"\n]")  # 重新添加结尾的 ']'
            else:  # 如果文件为空
                file.write(
                    json.dumps([data], indent=4).encode()
                )  # 创建新文件并写入数组
    except FileNotFoundError:
        with open(filename, "wb") as file:  # 如果文件不存在，创建并写入
            file.write(json.dumps([data], indent=4).encode())


def extract_str(text):
    try:
        xx = text["content"]
    except:
        raise Exception(text)
    xxx = xx.split("**Negative Prompt:**", 1)

    prompt = (
        xxx[0]
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
    )
    negative_prompt = (
        xxx[1]
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
    )

    return prompt, negative_prompt


def generate_prompt(path, save_path, name):
    with open(f"{path}/{name}.txt", "r", encoding="utf8") as file:
        # 初始化行数计数器
        line_number = 0
        lines = file.readlines()
        messages = []
        # 循环输出每一行内容
        prompt_json_save_path = os.path.join(save_path, f"{name}.json")
        for line in lines:
            line_number += 1
            print(f"正在处理第{line_number}段")
            if memory and os.path.exists(prompt_json_save_path):
                with open(prompt_json_save_path, "r", encoding="utf-8") as file:
                    prompt_data = json.load(file)
                if line_number <= len(prompt_data):
                    print(f"使用记忆：第{line_number}段")
                    continue
                else:
                    print("加载缓存数据")
                    with open(
                        f"{save_path}/{name}messages.json", "r", encoding="utf-8"
                    ) as f:
                        messages = json.load(f)
            text = f"第{line_number}段：" + line.strip()
            if line_number == 1:
                with open(f"{name}prompt.txt", "r", encoding="utf8") as f:
                    messages = [
                        {
                            "role": "system",
                            "content": f.read(),
                        }
                    ]

            result, message = Main().prompt_generation_chatgpt(text, messages)
            prompt, negative_prompt = extract_str(message)
            write_to_json(
                {"prompt": prompt, "negative_prompt": negative_prompt},
                prompt_json_save_path,
            )
            messages = result + [message]
            with open(f"{save_path}/{name}messages.json", "w") as f:
                f.write(json.dumps(messages))


if __name__ == "__main__":
    generate_prompt()
