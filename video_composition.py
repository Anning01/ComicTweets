#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2023/08/01 14:45
# @file:app.py
import os

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

if imagemagick_path:
    os.environ["IMAGEMAGICK_BINARY"] = rf"{imagemagick_path}"

from moviepy.editor import (
    AudioFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    ImageClip,
)
import numpy as np


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
        picture_path_list = sorted(
            [
                os.path.join(picture_path_path, name)
                for name in os.listdir(picture_path_path)
                if name.endswith(".png")
            ]
        )
        audio_path_list = sorted(
            [
                os.path.join(audio_path_path, name)
                for name in os.listdir(audio_path_path)
                if name.endswith(".mp3")
            ]
        )
        srt_path_list = sorted(
            [
                os.path.join(audio_path_path, name)
                for name in os.listdir(audio_path_path)
                if name.endswith(".srt")
            ]
        )
        for index, value in enumerate(picture_path_list):
            audio_clip = AudioFileClip(audio_path_list[index])
            img_clip = ImageClip(picture_path_list[index]).set_duration(audio_clip.duration)

            img_clip = img_clip.set_position(("center", "center")).set_duration(
                audio_clip.duration
            )

            # 解析对应的SRT文件
            subtitles = self.parse_srt(srt_path_list[index])
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
            clips.append(clip)
            os.makedirs(file_path, exist_ok=True)
            clip.write_videofile(
                os.path.join(file_path, f"{index}.mp4"), fps=24, audio_codec="aac"
            )
            print(f"-----------生成第{index}段视频-----------")
        print(f"-----------开始合成视频-----------")
        final_clip = concatenate_videoclips(clips)
        video_path = os.path.join(file_path, f"{name}.mp4")
        final_clip.write_videofile(video_path, fps=24, audio_codec="aac")
        return video_path

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

    def fl_up(self, gf, t):
        # 获取原始图像帧
        frame = gf(t)

        # 进行滚动效果，将图像向下滚动50像素
        height, width = frame.shape[:2]
        scroll_y = int(t * 10)  # 根据时间t计算滚动的像素数
        new_frame = np.zeros_like(frame)

        # 控制滚动的范围，避免滚动超出图像的边界
        if scroll_y < height:
            new_frame[: height - scroll_y, :] = frame[scroll_y:, :]

        return new_frame


if __name__ == "__main__":
    m = Main()
    picture_path_path = os.path.abspath(f"./images/千金")
    audio_path_path = os.path.abspath(f"./participle/千金")
    name = "千金"
    save_path = os.path.abspath(f"./video/千金")
    m.merge_video(picture_path_path, audio_path_path, name, save_path)
