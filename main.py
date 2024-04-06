# 第一步 分词
import asyncio
import json
import os

import yaml

from char2voice import create_voice_srt_new2
from extract_role import extract_potential_names
from participle import participle
from prompt import generate_prompt
from sd import Main as sd
from video_composition import Main as vc

with open("config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)
name = config["book"]["name"]
memory = config["book"]["memory"]

if not name:
    raise Exception("请输入书名")
if not os.path.exists(f"{name}.txt"):
    raise Exception("请将小说文件放入根目录")

print("---------------正在分词...---------------")
with open(f"{name}.txt", "r", encoding="utf-8") as f:
    novel = f.read().replace("\n", "").replace("\r", "").replace("\r\n", "")

path = os.path.join("participle", name)
os.makedirs(path, exist_ok=True)

participle_path = os.path.join(path, f"{name}.txt")
if memory and os.path.exists(participle_path):
    print("---------------读取缓存分词---------------")
else:
    with open(participle_path, "w", encoding="utf-8") as f:
        f.writelines(participle(novel))

print("---------------开始生成语音字幕---------------")
with open(participle_path, "r", encoding="utf8") as file:
    # 初始化行数计数器
    line_number = 0
    lines = file.readlines()
    messages = []
    # 循环输出每一行内容
    index = 0
    for line in lines:
        if (
                memory
                and os.path.exists(os.path.join(path, f"{index}.mp3"))
                and os.path.exists(os.path.join(path, f"{index}.srt"))
        ):
            print(f"---------------读取缓存语音字幕---------------")
        else:
            create_voice_srt_new2(index, line, path)
        index += 1

print("---------------开始提取角色---------------")
role_path = os.path.join(path, f"{name}.txt")
with open(role_path, "r", encoding="utf8") as f:
    novel_text = f.read().replace("\n", "").replace("\r", "").replace("\r\n", "")

# 提取文本中的潜在人名
names = extract_potential_names(novel_text)

text_ = ""
for n in names:
    text_ += f"- {n}\n"

with open("prompt.txt", "r", encoding="utf8") as f:
    prompt_text = f.read()

with open(f"{name}prompt.txt", "w", encoding="utf8") as f:
    f.write(prompt_text + text_)

print("---------------开始生成提示词---------------")
generate_prompt(path, path, name)

print("---------------开始异步生成生成图片---------------")
obj_path = os.path.join(path, f"{name}.json")
with open(obj_path, "r", encoding="utf-8") as f:
    obj_list = json.load(f)
asyncio.run(sd().draw_picture(obj_list, name))

print("---------------开始合成视频---------------")
m = vc()
picture_path_path = os.path.abspath(f"./images/{name}")
audio_path_path = os.path.abspath(f"./participle/{name}")
save_path = os.path.abspath(f"./video/{name}")
m.merge_video(picture_path_path, audio_path_path, name, save_path)
