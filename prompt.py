import json
import os
import re

import aiofiles

from api2d import Main
from chatgpt import Main as GPT
from load_config import get_yaml_config, check_file_exists, print_tip
from translate import Sample as translate

config = get_yaml_config()
memory = config["book"]["memory"]
is_translate = config["potential"]["translate"]
role_enabled = config["stable_diffusion"]["role"]
max_token = config["chatgpt"]["max_token"]


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

def remove_chinese_characters(text):
    # 正则表达式匹配所有中文字符
    # Unicode范围：\u4e00-\u9fff 基本的汉字范围
    # 扩展范围：\u3400-\u4dbf, \u20000-\u2a6df, \u2a700-\u2b73f, \u2b740-\u2b81f, \u2b820-\u2ceaf, \uf900-\ufaff, \u2f800-\u2fa1f
    pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u2f800-\u2fa1f]')
    # 使用re.sub()函数替换匹配到的字符为空字符串
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def extract_str(text):
    xxx = text

    prompt = (
        xxx
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("Prompt:", "")
        .replace("\n", "")
        .replace("\r","")
        .replace('\"', '')
        .replace("**","")
        .replace("   ","")
    )

    return prompt


async def process_line(line, line_number, prompt_json_save_path, messages_save_path, name, path):
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
        return await process_line(line, line_number, prompt_json_save_path, messages_save_path, name, path)
    else:
        prompt, negative_prompt = extract_str(message["content"])
        obj = {"prompt": prompt, "negative_prompt": negative_prompt}

        if role_enabled:
            # 固定人物
            if os.path.join(path, "role.json"):
                with open(os.path.join(path, "role.json"), "r", encoding="utf-8") as file:
                    role_data = json.load(file)
                for role in role_data:
                    roles = []
                    if role["name"] in text:
                        roles.append(role["name"])
                    obj["role"] = roles

        write_to_json(obj, prompt_json_save_path)
        messages = result + [message]
        with open(messages_save_path, "w") as f:
            f.write(json.dumps(messages))
        return 

async def process_line2(line, line_number, prompt_json_save_path, messages_save_path, name, path):
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
        with open(f"{name}prompt.txt", "r", encoding="utf-8") as f:
            messages = [
                {
                    "role": "system",
                    "content": f.read(),
                }
            ]

    result, message, total_tokens = GPT().chat(text, messages)
    await print_tip(f"当前total_tokens:{total_tokens}")
    if total_tokens >= max_token:
        # token 已经达到上限 重新请求GPT 清空之前的记录
        os.remove(messages_save_path)
        return await process_line(line, line_number, prompt_json_save_path, messages_save_path, name, path)
    else:
        prompt = extract_str(message)
        obj = {"prompt": 'best quality:1.37,4k,8k,highres,masterpiece,ultra-detailed,(HD photography),'+prompt, 
               "negative_prompt": "nsfw,EasyNegative,dark skin:1.5,muscular,(suntan:2),dark_skinned female,(sleeves:2),(tattoo:2),(sunglasses:2),(inverted nipples),(mutated:2),(worst quality:2),(low quality:2),(normal quality:2),lowres,blurry,((nasolabial folds):1.2),grayscale,jpeg artifacts,monochrome,non-linear background,out of frame,paintings,poorly drawn,semi-realistic,sepia,sketches,unclear architectural outline,asymmetric eyes,bad anatomy,cloned,crooked teeth,deformed,dehydrated,disfigured,double nipples,duplicate,extra arms,extra fingers,extra legs,extra limbs,long fingers,long neck,malformed limbs,missing arms,missing legs,missing teeth,more than five fingers on one hand:1.5,more than two arm per body:1.5,more than two leg per body:1.5,mutated,mutation,mutilated,odd eyes,ugly,(artist name:2),(logo:2),(text:2),(watermark:2),acnes,age spot,dark spots,fused,giantess,mole,fat female,skin blemishes,skin spots,animal ears,elf-ears,earrings,childish,morbid"}
        
        if role_enabled:
            # 固定人物
            if os.path.join(path, "role.json"):
                with open(os.path.join(path, "role.json"), "r", encoding="utf-8") as file:
                    role_data = json.load(file)
                roles = []
                for role in role_data:
                    if role["name"] in text:
                        roles.append(role["name"])
                obj["role"] = roles
        write_to_json(obj, prompt_json_save_path)
        messages = result
        with open(messages_save_path, "w") as f:
            f.write(json.dumps(messages))
        return


async def translates(text, line_number, prompt_json_save_path, path):
    is_exists = await check_file_exists(prompt_json_save_path)
    if memory and is_exists:
        with open(prompt_json_save_path, "r", encoding="utf-8") as file:
            prompt_data = json.load(file)
        if line_number <= len(prompt_data):
            return
    prompt = translate.main(text)
    obj = {"prompt": 'best quality,4k,8k,highres,masterpiece,ultra-detailed,(realistic,photorealistic,photo-realistic:1.37)'+prompt, 
           "negative_prompt": "nsfw,(low quality,normal quality,worst quality,jpeg artifacts),cropped,monochrome,low saturation,((watermark)),(white letters),dark skin:1.5,muscular,(suntan:1.2),dark_skinned female,(sleeves:1.2),(tattoo:1.2),(sunglasses:1.2),(inverted nipples),(mutated:2),blurry,((nasolabial folds):1.2),grayscale,jpeg artifacts,monochrome,non-linear background,out of frame,paintings,poorly drawn,semi-realistic,sepia,sketches,unclear architectural outline,asymmetric eyes,bad anatomy,cloned,crooked teeth,deformed,dehydrated,disfigured,duplicate,,long neck,malformed limbs,missing arms,missing legs,missing teeth,more than two leg per body:1.5,mutated,mutation,mutilated,odd eyes,ugly,(text:2),acnes,age spot,dark spots,fused,giantess,mole,fat female,skin blemishes,skin spots,animal ears,elf-ears,earrings,childish,morbid"}
    if role_enabled:
        # 固定人物
        if os.path.join(path, "role.json"):
            with open(os.path.join(path, "role.json"), "r", encoding="utf-8") as file:
                role_data = json.load(file)
            roles = []
            for role in role_data:
                if role["name"] in text:
                    roles.append(role["name"])
            obj["role"] = roles
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
                    await translates(line, line_number, prompt_json_save_path, path)
                else:
                    await process_line2(line, line_number, prompt_json_save_path, messages_save_path, name, path)

if __name__ == "__main__":
    generate_prompt()
