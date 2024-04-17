import json
import os

import aiofiles

from api2d import Main
from load_config import get_yaml_config, check_file_exists, print_tip
from translate import Sample as translate

config = get_yaml_config()
memory = config["book"]["memory"]
is_translate = config["potential"]["translate"]


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
        .replace("Prompt:", "")
        .replace("\n", "")
    )
    negative_prompt = (
        xxx[1]
        .replace("**Negative Prompt:**", "")
        .replace("Prompt:", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
    )

    return prompt, negative_prompt


async def process_line(line, line_number, prompt_json_save_path, messages_save_path, name):
    await print_tip(f"正在处理第{line_number}段")
    is_exists = await check_file_exists(prompt_json_save_path)
    is_message_exists = await check_file_exists(messages_save_path)
    if memory and is_exists:
        with open(prompt_json_save_path, "r", encoding="utf-8") as file:
            prompt_data = json.load(file)
        if line_number <= len(prompt_data):
            await print_tip(f"使用缓存：跳过第{line_number}段")
            return 
        else:
            if is_message_exists:
                async with aiofiles.open(
                    messages_save_path, "r", encoding="utf-8"
                ) as f:
                    content = await f.read()
                    messages = json.loads(content)
    text = f"第{line_number}段：" + line.strip()
    if not is_message_exists:
        with open(f"{name}prompt.txt", "r", encoding="utf8") as f:
            messages = [
                {
                    "role": "system",
                    "content": f.read(),
                }
            ]

    result, message, total_tokens = await Main().prompt_generation_chatgpt(text, messages)
    await print_tip(f"当前total_tokens:{total_tokens}")
    if total_tokens >= 16385:
        # token 已经达到上限 重新请求GPT 清空之前的记录
        os.remove(messages_save_path)
        return await process_line(line, line_number, prompt_json_save_path, messages_save_path, name)
    else:
        prompt, negative_prompt = extract_str(message)
        obj = {"prompt": prompt, "negative_prompt": negative_prompt}

        # 创建一个后台任务以非阻塞方式执行绘图函数
        # asyncio.create_task(SD().draw_picture(obj, line_number, name))

        write_to_json(obj, prompt_json_save_path)
        messages = result + [message]
        with open(messages_save_path, "w") as f:
            f.write(json.dumps(messages))
        return 


async def translates(text, line_number, prompt_json_save_path):
    is_exists = await check_file_exists(prompt_json_save_path)
    if memory and is_exists:
        with open(prompt_json_save_path, "r", encoding="utf-8") as file:
            prompt_data = json.load(file)
        if line_number <= len(prompt_data):
            return
    prompt = translate.main(text)
    obj = {"prompt": prompt, "negative_prompt": "nsfw,(low quality,normal quality,worst quality,jpeg artifacts),cropped,monochrome,lowres,low saturation,((watermark)),(white letters)"}
    write_to_json(obj, prompt_json_save_path)


async def generate_prompt(path, save_path, name):
    await print_tip("开始生成提示词")
    async with aiofiles.open(f"{path}/{name}.txt", "r", encoding="utf8") as file:
        # 初始化行数计数器
        lines = await file.readlines()
        # 循环输出每一行内容
        prompt_json_save_path = os.path.join(save_path, f"{name}.json")
        messages_save_path = os.path.join(save_path, f"{name}messages.json")
        for line_number, line in enumerate(lines, start=1):
            if line:
                if is_translate:
                    await translates(line, line_number, prompt_json_save_path)
                else:
                    await process_line(line, line_number, prompt_json_save_path, messages_save_path, name)

if __name__ == "__main__":
    generate_prompt()
