#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/09 14:44
# @file:voice_caption.py
# 将图片和文字，字幕 一次性合成
import json
import os.path
import random
import re
from datetime import datetime
import subprocess
import asyncio

import aiofiles
import edge_tts

from char2voice import create_voice_srt_new2
from load_config import get_yaml_config, check_file_exists, print_tip

config = get_yaml_config()
limit = config["audio"]["limit"]
role = config["audio"]["role"]
rate = config["audio"]["rate"]
volume = config["audio"]["volume"]
bgm = config["audio"]["bgm"]
main_db = config["audio"]["main_db"]
bgm_db = config["audio"]["bgm_db"]
once = config["video"]["once"]
memory = config["book"]["memory"]


async def spilt_str2(s, t, k=limit):
    """
    :param s: 切片文本
    :param t: 切分前时间
    :param k: 切分最大字数
    :return:  新的切片信息

    @ samples
        s = "并且觉醒天赋 得到力量 对抗凶兽 觉醒天赋 便是人人在十八岁时能以血脉沟通沟通 觉醒天赋"
        t = "00:00:35,184 --> 00:00:42,384"
        k = 15
    """

    async def time2second(ti):
        """
        :param ti: 输入时间， 格式示例：00:02:56,512
        :return: float
        """
        a, b, _c = ti.split(":")
        c, d = _c.split(",")

        a, b, c, d = int(a), int(b), int(c), int(d)

        second = a * 3600 + b * 60 + c + d / 1000

        return second

    async def second2time(si):
        hours = int(si // 3600)
        minutes = int((si % 3600) // 60)
        seconds = int(si % 60)
        milliseconds = round((si % 1) * 1000)

        v = "00"
        u = "000"
        a = v[: 2 - len(str(hours))] + str(hours)
        b = v[: 2 - len(str(minutes))] + str(minutes)
        c = v[: 2 - len(str(seconds))] + str(seconds)
        d = u[: 3 - len(str(milliseconds))] + str(milliseconds)

        return f"{a}:{b}:{c},{d}"

    ss = s.split(" ")
    ss_valid = []

    # todo 将所有片段设置成不超过15
    for _ss in ss:
        if len(_ss) > k:

            # 暴力截断几段
            e = len(_ss) // k + 1
            n_e = len(_ss) // e + 1

            for _i in range(e):
                if _i == e - 1:
                    ss_valid.append(_ss[n_e * _i :])
                else:
                    ss_valid.append(_ss[n_e * _i : n_e * (_i + 1)])
        else:
            ss_valid.append(_ss)

    # todo 片段合并
    tmp = ""
    new_ss = []
    for i in range(len(ss_valid)):
        tmp += ss_valid[i]

        if i < len(ss_valid) - 1:
            if len(tmp + ss_valid[i + 1]) > k:
                new_ss.append(tmp)
                tmp = ""
            else:
                continue
        else:
            new_ss.append(tmp)
            tmp = ""

    # 分配时间戳
    t1, t2 = t.split("-->")
    ft1 = await time2second(t1)
    ft2 = await time2second(t2)
    ftd = ft2 - ft1

    # 转换成秒数
    all_str = " ".join(new_ss)

    tt_s = 0
    line_srt = []
    for z in new_ss:
        tt_e = len(z) + tt_s

        # 文章最后一句异常处理
        if len(all_str) * ftd == 0:
            continue

        t_start = tt_s / len(all_str) * ftd
        t_end = tt_e / len(all_str) * ftd
        t_start = round(t_start, 3)
        t_end = round(t_end, 3)

        rec_s = await second2time(ft1 + t_start)
        rec_e = await second2time(ft1 + t_end)

        cc = (f"{rec_s} --> {rec_e}", z)
        line_srt.append(cc)

        tt_s = tt_e + 1

    return line_srt


async def time_difference(time1, time2):
    time_format = r"%H:%M:%S,%f"
    time1 = datetime.strptime(time1, time_format)
    time2 = datetime.strptime(time2, time_format)

    # 计算时间差
    delta = time2 - time1
    time_diff = str(delta).replace(".", ",")[:11]
    return time_diff


async def load_srt_new(filename, flag=True):
    time_format = r"(\d{2}:\d{2}:\d{2}),\d{3} --> (\d{2}:\d{2}:\d{2}),\d{3}"

    n = 0  # srt 文件总行数
    index = 0  # strs 文字串移动下标
    line_tmp = ""  # 每个时间区间后的字数累计
    count_tmp = 0  # 每个时间区间后的字数行计数
    new_srt = []

    async with aiofiles.open(filename, mode="r", encoding="utf-8") as f3:
        f_lines = await f3.readlines()
        for line in f_lines:
            line = line.strip("\n")
            n += 1

            # 写入新的数据
            #   1)当出现在文本末写入一次
            if n == len(f_lines):
                new_srt_line = await spilt_str2(line_tmp, t_line_cur)
                new_srt.append(new_srt_line)

            #   2）当新的一行是数字时，srt语句段写入
            # case1: 判断新的一行是不是数字
            if line.isdigit():
                if flag:
                    print(line)
                if n > 1:
                    new_srt_line = await spilt_str2(line_tmp, t_line_cur)
                    new_srt.append(new_srt_line)
                continue

            # case2: 判断新的一行是不是时间段
            if re.match(time_format, line):
                t_line_cur = line
                # reset line_tmp
                line_tmp = ""
                count_tmp = 0
                continue

            # case3: 判断新的一行是空格时
            if len(line) == 0:
                continue

            # case4: 新的一行不属于上面其中之一
            line_std = line.replace(" ", "")
            if flag:
                print(f"{line}\n{line_std}")

            if count_tmp:
                line_tmp += " " + line_std
            else:
                line_tmp += line_std
            count_tmp += 1

    srt = []
    for _line in new_srt:
        for _l in _line:
            srt.append(_l)
    return srt


async def save_srt(filename, srt_list):
    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
        for _li, _l in enumerate(srt_list):
            if _li == len(srt_list) - 1:
                info = "{}\n{}\n{}".format(_li + 1, _l[0], _l[1])
            else:
                info = "{}\n{}\n{}\n\n".format(_li + 1, _l[0], _l[1])
            await f.write(info)


async def srt_regen_new(f_srt, f_save, flag):
    srt_list = await load_srt_new(f_srt, flag)
    await save_srt(f_save, srt_list)


class CustomSubMaker(edge_tts.SubMaker):
    """重写此方法更好的支持中文"""

    async def generate_cn_subs(self, text):

        PUNCTUATION = ["，", "。", "！", "？", "；", "：", "”", ",", "!", "…", "+", "-", "······", "“"]

        def clause(self):
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
                    text_list.append(text[start:i])
                    start = i
                i += 1
            return text_list

        self.text_list = clause(self)
        if len(self.subs) != len(self.offset):
            raise ValueError("subs and offset are not of the same length")
        data = "WEBVTT\r\n\r\n"
        j = 0
        for text in self.text_list:
            text = await self.remove_non_chinese_chars(text)
            try:
                start_time = self.offset[j][0]
            except IndexError:
                return data
            try:
                while self.subs[j + 1] in text:
                    j += 1
            except IndexError:
                pass
            data += edge_tts.submaker.formatter(start_time, self.offset[j][1], text)
            j += 1
        return data

    async def remove_non_chinese_chars(self, text):
        # 使用正则表达式匹配非中文字符和非数字
        # pattern = re.compile(r"[^\u4e00-\u9fff0-9]+")
        pattern = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9]+")
        # 使用空字符串替换匹配到的非中文字符和非数字
        cleaned_text = re.sub(pattern, "", text)
        return cleaned_text


async def edge_gen_srt2(f_txt, f_mp3, f_vtt, f_srt, p_voice, p_rate, p_volume) -> None:
    content = f_txt
    communicate = edge_tts.Communicate(
        text=content, voice=p_voice, rate=p_rate, volume=p_volume
    )
    sub_maker = CustomSubMaker()
    async with aiofiles.open(f_mp3, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                await file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub(
                    (chunk["offset"], chunk["duration"]), chunk["text"]
                )

    async with aiofiles.open(f_vtt, "w", encoding="utf-8") as file:
        content_to_write = await sub_maker.generate_cn_subs(content)
        # content_to_write = sub_maker.generate_subs()
        await file.write(content_to_write)

    # vtt -》 srt
    idx = 1  # 字幕序号
    with open(f_srt, "w", encoding="utf-8") as f_out:
        for line in open(f_vtt, encoding="utf-8"):
            if "-->" in line:
                f_out.write("%d\n" % idx)
                idx += 1
                line = line.replace(".", ",")  # 这行不是必须的，srt也能识别'.'
            if idx > 1:  # 跳过header部分
                f_out.write(line)


# 合并文件夹下所有MP3文件为一个音频文件
async def merge_bgm(bgm_folder):
    mp3_files = [
        os.path.join(bgm_folder, mp3_file)
        for mp3_file in os.listdir(bgm_folder)
        if mp3_file.endswith(".mp3")
    ]
    random.shuffle(mp3_files)  # 随机化列表中元素的顺序

    with open("bgm_list.txt", "w", encoding="utf-8") as filelist:
        for mp3_file in mp3_files:
            filelist.write(f"file '{mp3_file}'\n")

    # with open('bgm_list.txt', 'w', encoding="utf-8") as filelist:
    #     for mp3_file in os.listdir(bgm_folder):
    #         if mp3_file.endswith('.mp3'):
    #             filelist.write(f"file '{os.path.join(bgm_folder, mp3_file)}'\n")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            "bgm_list.txt",
            "-c",
            "copy",
            "merged_bgm.mp3",
        ],
        check=True,
    )
    os.remove("bgm_list.txt")


# 获取媒体文件长度
async def get_media_length(file_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return float(result.stdout)


# 获取音频文件的详细信息（比特率、采样率、声道数）
async def get_audio_details(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate,sample_rate,channels",
        "-of",
        "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    details = {
        "bit_rate": int(metadata["streams"][0]["bit_rate"]),
        "sample_rate": int(metadata["streams"][0]["sample_rate"]),
        "channels": int(metadata["streams"][0]["channels"]),
    }
    return details


# 循环BGM以匹配主音轨长度，然后与主音轨混合
async def mix_main_and_bgm(main_audio, bgm_file, save_dir):
    await merge_bgm("bgm")
    main_length = await get_media_length(main_audio)
    bgm_length = await get_media_length(bgm_file)
    main_volume = f"{main_db}dB"
    bgm_volume = f"{bgm_db}dB"
    # 计算BGM需要循环的次数
    loop_count = int(main_length // bgm_length) + 1 if bgm_length < main_length else 1

    # 如果需要，循环BGM
    if loop_count > 1:
        with open("looped_bgm_list.txt", "w", encoding="utf-8") as loop_file:
            for _ in range(loop_count):
                loop_file.write(f"file '{bgm_file}'\n")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "looped_bgm_list.txt",
                "-c",
                "copy",
                "looped_bgm.mp3",
            ],
            check=True,
        )
        looped_bgm = "looped_bgm.mp3"
        os.remove("looped_bgm_list.txt")
    else:
        looped_bgm = bgm_file

    audio_details = await get_audio_details(main_audio)

    # 采样率、声道和比特率
    sample_rate = str(audio_details["sample_rate"])
    channels = str(audio_details["channels"])
    bitrate = str(audio_details["bit_rate"])
    # 转换循环后的BGM为单声道，采样率调整为24kHz
    converted_bgm = os.path.join(save_dir, "bgm_converted.mp3")

    subprocess.run(
        ["ffmpeg", "-y", "-i", looped_bgm, "-ac", str(channels), "-ar", str(sample_rate), converted_bgm],
        check=True
    )

    output_file = os.path.join(save_dir, "out.mp3")
    # 混合主音轨和已转换的BGM
    # subprocess.run([
    #     'ffmpeg', '-i', main_audio, '-i', 'bgm_converted.mp3',
    #     '-filter_complex',
    #     f"[0:a]aformat=sample_rates=24000:channel_layouts=mono,volume={main_volume}[a0];[1:a]aformat=sample_rates=24000:channel_layouts=mono,volume={bgm_volume}[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
    #     '-map', '[aout]', '-ac', '1', '-ar', '24000', '-y', output_file
    # ], check=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            main_audio,
            "-i",
            converted_bgm,
            "-filter_complex",
            f"[0:a]aformat=sample_rates={sample_rate}:channel_layouts=stereo,volume={main_volume}[a0];[1:a]aformat=sample_rates={sample_rate}:channel_layouts=stereo,volume={bgm_volume}[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
            "-map",
            "[aout]",
            "-ac",
            channels,
            "-ar",
            sample_rate,
            "-b:a",
            bitrate,
            output_file,
        ],
        check=True,
    )
    # 清理临时文件
    os.remove("merged_bgm.mp3")
    os.remove(converted_bgm)
    if loop_count > 1:
        os.remove("looped_bgm.mp3")
    os.replace(output_file, main_audio)


async def picture_processing_time(filename, section_path, save_dir, name):
    subtitles = []  # 存储最终结果的列表
    text = []  # 临时存储当前字幕块的文本行
    timecode = None  # 初始化时间码变量

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()  # 移除行首尾的空白字符

            if line.isdigit():  # 跳过字幕编号行
                continue

            if "-->" in line:  # 检测时间码行
                if text:  # 如果前一个字幕块的文本已经读取，存储前一个字幕块
                    subtitles.append((timecode, " ".join(text)))
                    text = []  # 重置文本列表为下一个字幕块做准备
                timecode = line  # 更新时间码

            elif line:  # 非空行即为字幕文本行
                text.append(line)

            # 无需处理空行，因为它们在这个逻辑中不起作用

        # 添加文件末尾的最后一个字幕块（如果有）
        if text:
            subtitles.append((timecode, " ".join(text)))
    with open(section_path, "r", encoding="utf-8") as f:
        section_list = f.readlines()
    section_time_list = []
    index_ = 0
    time_ = "00:00:00,000"
    for si, section in enumerate(section_list):
        if len(section_list) == si + 1:
            # 最后这段不处理 默认使用剩余所有time
            next_start_time = subtitles[-1][0].split(" --> ")[1]
            diff = await time_difference(time_, next_start_time)
            section_time_list.append(diff)
            break
        content_ = await CustomSubMaker().remove_non_chinese_chars(section)
        for i, v in enumerate(subtitles):
            if i <= index_:
                continue
            if v[1] not in content_:
                next_start_time = v[0].split(" --> ")[0]
                diff = await time_difference(time_, next_start_time)
                section_time_list.append(diff)
                index_ = i
                time_ = next_start_time
                break
            else:
                content_.replace(v[1], "")
    with open(os.path.join(save_dir, f"{name}time.txt"), "w", encoding="utf-8") as f3:
        f3.write(str(section_time_list))


async def create_voice_srt_new3(
    name, file_txt, save_dir, p_voice=role, p_rate=rate, p_volume=volume
):
    mp3_name = f"{name}.mp3"
    vtt_name = f"{name}.vtt"
    srt_name = f"{name}.tmp.srt"
    srt_name_final = f"{name}.srt"

    file_mp3 = os.path.join(save_dir, mp3_name)
    file_vtt = os.path.join(save_dir, vtt_name)
    file_srt = os.path.join(save_dir, srt_name)
    file_srt_final = os.path.join(save_dir, srt_name_final)
    mp3_exists = await check_file_exists(file_mp3)
    srt_exists = await check_file_exists(file_srt_final)
    time_exists = await check_file_exists(os.path.join(save_dir, f"{name}time.txt"))
    if mp3_exists and srt_exists and time_exists:
        return
    await edge_gen_srt2(
        file_txt, file_mp3, file_vtt, file_srt, p_voice, p_rate, p_volume
    )

    await srt_regen_new(file_srt, file_srt_final, False)

    await picture_processing_time(
        file_srt_final, os.path.join(save_dir, f"{name}.txt"), save_dir, name
    )
    #  删除其他生成文件
    os.remove(file_vtt)
    os.remove(file_srt)

    if bgm:
        # 如果使用bgm
        await mix_main_and_bgm(file_mp3, "merged_bgm.mp3", save_dir)

    return file_mp3, file_srt_final


async def voice_srt(participle_path, path, name_path, name):
    await print_tip("开始生成语音字幕")
    if once:
        with open(name_path, "r", encoding="utf-8") as f:
            content = f.read()
        max_attempts = 10  # 设置最大尝试次数
        attempts = 0  # 初始化尝试次数计数器
        while attempts < max_attempts:
            try:
                # 尝试执行可能出错的操作
                await create_voice_srt_new3(name, content, path)
                break  # 如果成功，则跳出循环
            except Exception as e:
                # 捕获到异常，打印错误信息，并决定是否重试
                print(f"尝试生成语音字幕时出错: {e}")
                attempts += 1  # 增加尝试次数
                await asyncio.sleep(10)  # 等待一段时间后重试，避免立即重试

        if attempts == max_attempts:
            raise Exception("尝试生成语音字幕失败次数过多，停止重试。")
    else:
        async with aiofiles.open(participle_path, "r", encoding="utf8") as file:
            lines = await file.readlines()
            # 循环输出每一行内容
            index = 1
            for line in lines:
                if line:
                    mp3_exists = await check_file_exists(
                        os.path.join(path, f"{index}.mp3")
                    )
                    srt_exists = await check_file_exists(
                        os.path.join(path, f"{index}.srt")
                    )
                    if memory and mp3_exists and srt_exists:
                        await print_tip(f"使用缓存，读取第{index}段语音字幕")
                    else:
                        await create_voice_srt_new2(index, line, path)
                    index += 1


if __name__ == "__main__":
    save_dir = './'
    asyncio.run(mix_main_and_bgm("./20075.mp3", "merged_bgm.mp3", save_dir))

