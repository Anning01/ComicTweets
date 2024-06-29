import asyncio
import os

from load_config import get_yaml_config, print_tip, check_file_exists

import aiofiles
from aiofiles import os as aio_os

from utils.english_segment import split_text_into_paragraphs, split_paragraphs_into_sentences, \
    split_spain_paragraphs_into_sentences

config = get_yaml_config()
min_words = config["potential"]["min_words"]
max_words = config["potential"]["max_words"]
memory = config["book"]["memory"]
language = config["book"]["language"]


# 根据小说文本进行分词
async def combine_strings(strings):
    combined = []
    current_srt = ""
    for s in strings:
        if min_words <= len(current_srt + s) <= max_words:
            combined.append(current_srt + s + "\n")
            current_srt = ""
        elif len(current_srt) > max_words:
            combined.append(current_srt + "\n")
            current_srt = s
        else:
            current_srt += s
    if current_srt:
        combined.append(current_srt + "\n")
    return combined


async def participle(text):
    PUNCTUATION = ["，", "。", "！", "？", "；", "：", "”", ",", "!", "…"]

    # async def clause():
    #     start = 0
    #     i = 0
    #     text_list = []
    #     while i < len(text):
    #         if text[i] in PUNCTUATION:
    #             try:
    #                 while text[i] in PUNCTUATION:
    #                     i += 1
    #             except IndexError:
    #                 pass
    #             text_list.append(text[start:i].strip())
    #             start = i
    #         i += 1
    #     return text_list
    #
    # text_list = await clause()
    # result = await combine_strings(text_list)
    # return result
    async def clause():
        start = 0
        i = 0
        text_list = []
        while i < len(text):
            if text[i] in PUNCTUATION:
                try:
                    while text[i] in PUNCTUATION:
                        i += 1
                except IndexError:
                    pass
                text_list.append(text[start:i].strip())
                start = i
            i += 1
        return text_list

    if language == "zh":
        text_list = await clause()
        result = await combine_strings(text_list)
        return result
    elif language == "en":
        paragraphs = split_text_into_paragraphs(text)
        return [sentence + '\n' for sentence in split_paragraphs_into_sentences(paragraphs)]

    elif language == "es":
        paragraphs = split_text_into_paragraphs(text)
        return [sentence + '\n' for sentence in split_spain_paragraphs_into_sentences(paragraphs)]
    else:
        raise Exception("Unsupported language")



async def main(name_path, path, participle_path):
    await print_tip("正在分词")

    async with aiofiles.open(name_path, "r", encoding="utf-8") as f:
        content = await f.read()
        novel = content.replace("\n", "").replace("\r", "").replace("\r\n", "").replace("\u2003", "")
    await aio_os.makedirs(path, exist_ok=True)
    is_exists = await check_file_exists(participle_path)
    if memory and is_exists:
        await print_tip("读取缓存分词")
    else:
        async with aiofiles.open(participle_path, "w", encoding="utf-8") as f:
            participles = await participle(novel)
            await f.writelines(participles)
    await print_tip("分词完成")


if __name__ == "__main__":
    with open("./斗破苍穹.txt", "r", encoding="utf-8") as f:
        novel = f.read().replace("\n", "").replace("\r", "").replace("\r\n", "").replace("\u2003", "")
    with open("./斗破苍穹txt.txt", "w", encoding="utf-8") as f:
        content = asyncio.run(participle(novel))
        f.writelines(content)
