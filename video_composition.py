#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2023/08/01 14:45
# @file:app.py
import ast
import os
import re
import subprocess

from load_config import get_yaml_config

config = get_yaml_config()
imagemagick_path = config["video"]["imagemagick_path"]
fontsize = config["video"]["fontsize"]
fontcolor = config["video"]["fontcolor"]
fontfile = config["video"]["fontfile"]
stroke_color = config["video"]["stroke_color"]
stroke_width = config["video"]["stroke_width"]
kerning = config["video"]["kerning"]
position = config["video"]["position"]
use_moviepy = config["video"]["use_moviepy"]
once = config["video"]["once"]

if imagemagick_path:
    os.environ["IMAGEMAGICK_BINARY"] = rf"{imagemagick_path}"

from moviepy.editor import (
    AudioFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    ImageClip,
)


class Main:

    def merge_video(
            self, picture_path_path: str, audio_path_path: str, name: str, file_path: str
    ):
        """
        :param picture_path_list: 图片路径列表
        :param audio_path_list: 音频路径列表
        :return:
        """
        clips = []

        def extract_number(filename):
            match = re.search(r'(\d+)', filename)
            if match:
                return int(match.group(0))
            return 0  # 如果文件名中没有数字，则默认为 0
        picture_path_list = sorted(
            [
                os.path.join(picture_path_path, name)
                for name in os.listdir(picture_path_path)
                if name.endswith(".png")
            ],
            key=lambda x: extract_number(os.path.basename(x))
        )
        if once:
            audio_path = os.path.join(audio_path_path, f"{name}.mp3")
            srt_path = os.path.join(audio_path_path, f"{name}.srt")
            time_file = os.path.join(audio_path_path, f"{name}time.txt")
            self.disposable_synthesis(picture_path_list, audio_path, srt_path, time_file, file_path, name)
        else:
            audio_path_list = sorted(
                [
                    os.path.join(audio_path_path, name)
                    for name in os.listdir(audio_path_path)
                    if name.endswith(".mp3")
                ],
                key=lambda x: extract_number(os.path.basename(x))
            )
            srt_path_list = sorted(
                [
                    os.path.join(audio_path_path, name)
                    for name in os.listdir(audio_path_path)
                    if name.endswith(".srt")
                ],
                key=lambda x: extract_number(os.path.basename(x))
            )
            if os.path.isfile(f"{file_path}/{name}.txt"):
                os.remove(f"{file_path}/{name}.txt")
            if os.path.exists(file_path):
                filelist = os.listdir(file_path)
                if len(filelist) != 0:  # 开始删除所有文件
                    for file in filelist:
                        os.remove(os.path.join(file_path, file))
                os.rmdir(file_path)

            for index, value in enumerate(picture_path_list, start=1):
                audio_clip = AudioFileClip(audio_path_list[index - 1])
                img_clip = ImageClip(value).set_duration(audio_clip.duration)

                img_clip = img_clip.set_position(("center", "center")).set_duration(
                    audio_clip.duration
                )
                if use_moviepy:
                    # 解析对应的SRT文件
                    subtitles = self.parse_srt(srt_path_list[index - 1])
                    # 为当前视频片段添加字幕
                    subs = [
                        self.create_text_clip(
                            img_clip,
                            sub["text"],
                            start=sub["start"],
                            duration=sub["end"] - sub["start"],
                        )
                        for sub in subtitles
                    ]
                    clip_with_subs = CompositeVideoClip([img_clip] + subs)
                    clip = clip_with_subs.set_audio(audio_clip)
                else:
                    clip = img_clip.set_audio(audio_clip)

                clips.append(clip)
                os.makedirs(file_path, exist_ok=True)
                video_path = os.path.join(file_path, f"{index}.mp4")
                clip.write_videofile(
                    video_path, fps=24, audio_codec="aac"
                )
                if not use_moviepy:
                    self.create_srt(
                        video_path, srt_path_list[index - 1], file_path, name
                    )
                    with open(f"{file_path}/{name}.txt", "a", encoding="utf-8") as f:
                        f.write(f"file '{video_path}'\n")
                print(f"-----------生成第{index}段视频-----------")
            print(f"-----------开始合成视频-----------")
            if use_moviepy:
                final_clip = concatenate_videoclips(clips)
                video_path = os.path.join(file_path, f"{name}.mp4")
                final_clip.write_videofile(video_path, fps=24, audio_codec="aac")
            else:
                self.mm_merge_video(file_path, name)

    def disposable_synthesis(self, picture_path_list, audio_path, srt_path, time_file, save_path, name):
        # 一次性合成图片视频字幕
        """
        ffmpeg -f concat -safe 0 -i filelist.txt -i audio.mp3 -vf "subtitles=subtitle_file.srt" -vsync vfr -pix_fmt yuv420p output.mp4
        """

        def convert_time_string(time_str):
            # 分割小时、分钟、秒和毫秒
            hours, minutes, seconds = time_str.split(':')
            seconds, milliseconds = seconds.split(',')

            # 将分割得到的字符串转换为数值
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)
            milliseconds = int(milliseconds)

            # 将时间转换为秒
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

            return total_seconds

        with open(time_file, "r", encoding="utf-8") as f:
            content = f.read()
        time_list = ast.literal_eval(content)
        # 首先创建图片文件
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, "filelist.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            for index, picture_path in enumerate(picture_path_list):
                f.write(f"file '{picture_path}'\n")
                if index < len(time_list):
                    f.write(f"duration {convert_time_string(time_list[index])}\n")
        out_path = os.path.join(save_path, f"{name}.mp4")
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", file_path,
            "-i", audio_path,
            "-vsync", "cfr",
            "-pix_fmt", "yuv420p",
            out_path
        ]
        subprocess.run(cmd, check=True)

        self.create_srt(out_path, srt_path, save_path, name)

    def create_srt(self, video_path, srt_path, file_path, name):
        """
        创建SRT字幕文件
        :param video_path: 视频文件路径
        :return:
        """
        out_path = os.path.join(file_path, f"out{name}.mp4")

        # 构建字体样式字符串，只包含颜色和大小
        style = f"Fontsize={fontsize},PrimaryColour=&H{fontcolor}"

        # 构建 FFmpeg 命令，不再设置字体文件路径
        if os.name == 'nt':
            # 由于绝对路径下win会报错 所以转换成相对路径
            proj_path = os.path.abspath("./")
            out_path = os.path.relpath(out_path, proj_path).replace("\\", "/")
            video_path = os.path.relpath(video_path, proj_path).replace("\\", "/")
            srt_path = os.path.relpath(srt_path, proj_path).replace("\\", "/")
            cmd = f"""ffmpeg -i {video_path} -vf subtitles={srt_path}:force_style={style} -c:a copy {out_path}"""
        else:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{srt_path}':force_style='{style}'",
                '-c:a', 'copy',
                out_path
            ]

        # 执行命令
        subprocess.run(cmd, check=True)
        os.replace(out_path, video_path)  # 用输出文件替换原始文件

    def parse_srt(self, srt_path):
        """
        解析SRT字幕文件
        :param srt_path: SRT文件路径
        :return: 字幕数据列表，每个字幕包含开始时间、结束时间和文本
        """
        subtitles = []
        with open(srt_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            for i in range(0, len(lines), 4):
                start_end = lines[i + 1].split(" --> ")
                start = self.srt_time_to_seconds(start_end[0].strip())
                end = self.srt_time_to_seconds(start_end[1].strip())
                text = lines[i + 2].strip()
                subtitles.append({"start": start, "end": end, "text": text})
        return subtitles

    def mm_merge_video(self, video_path, name):
        out_path = os.path.join(video_path, f"{name}.mp4")
        inputs_path = os.path.join(video_path, f"{name}.txt")
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i',
            f'{inputs_path}', '-c', 'copy',
            f'{out_path}'
        ])

    def srt_time_to_seconds(self, time_str):
        """
        将SRT时间格式转换为秒
        :param time_str: SRT时间字符串
        :return: 对应的秒数
        """
        hours, minutes, seconds = map(float, time_str.replace(",", ".").split(":"))
        return hours * 3600 + minutes * 60 + seconds

    def create_text_clip(self, img_clip, text, start, duration):
        """
        创建包含文字的TextClip
        :param text: 字幕文本
        :param start: 字幕开始时间
        :param duration: 字幕持续时间
        :return: TextClip对象
        """
        video_clip_height = img_clip.h  # 获取视频的高度

        txt_clip = TextClip(
            text,
            fontsize=fontsize,
            color=fontcolor,
            font=fontfile,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            kerning=kerning,
            method="label",
        )
        txt_clip = txt_clip.set_start(start).set_duration(duration)
        txt_clip = txt_clip.set_position(
            lambda t: (
                "center",
                max(
                    position * video_clip_height - t * 10, position * video_clip_height
                ),
            )
        )

        return txt_clip


if __name__ == "__main__":
    m = Main()
    picture_path_path = os.path.abspath(f"./images/test_image")
    audio_path_path = os.path.abspath(f"./participle/test_image")
    name = "test_image"
    save_path = os.path.abspath(f"./video/test_image")
    m.merge_video(picture_path_path, audio_path_path, name, save_path)
