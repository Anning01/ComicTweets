#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/06/15 23:39
# @file:video_filter.py


import os
import subprocess


def blend_videos(normal_video, particle_video, output_video, alpha=0.5):
    # 获取正常视频的时长
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', normal_video],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    normal_duration = float(result.stdout)

    # 创建一个临时调整后的粒子视频文件
    temp_particle_video = 'temp_particle.mp4'

    try:
        # 调整粒子视频长度
        ffmpeg_command_adjust = [
            'ffmpeg',
            '-i', particle_video,
            '-filter_complex',
            f'[0:v]loop=loop=-1:size=20000:start=0,setpts=N/FRAME_RATE/TB,trim=duration={normal_duration}[looped]',
            '-map', '[looped]',
            '-y',  # overwrite output file if it exists
            temp_particle_video
        ]
        subprocess.run(ffmpeg_command_adjust, check=True)

        # 合并正常视频和调整后的粒子视频
        ffmpeg_command_blend = [
            'ffmpeg',
            '-i', normal_video,
            '-i', temp_particle_video,
            '-filter_complex',
            f'[1:v]format=rgba,colorchannelmixer=aa={alpha}[particle];[0:v][particle]overlay',
            '-c:a', 'copy',
            '-y',  # overwrite output file if it exists
            output_video
        ]
        subprocess.run(ffmpeg_command_blend, check=True)

    finally:
        # 删除临时文件
        if os.path.exists(temp_particle_video):
            os.remove(temp_particle_video)


if __name__ == '__main__':

    # 示例使用
    normal_video = '成品/e/video/e_final.mp4'
    particle_video = '粒子特效/665_1718178291.mp4'
    output_video = 'output.mp4'
    alpha = 0.5  # 调整粒子视频透明度

    blend_videos(normal_video, particle_video, output_video, alpha)
