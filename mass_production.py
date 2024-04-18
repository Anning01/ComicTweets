# 编写此脚本的目的是为了批量生产 会将source_path下的文件生成到dest_path下
import asyncio
import os.path
import re
import subprocess

from load_config import get_yaml_config
from main import role
from translate import Sample as translate
from cover_drawing import add_watermark
from participle import main as participle
from prompt import generate_prompt
from sd import new_draw_picture
from voice_caption import voice_srt
from video_composition import Main as vc
from sd import Main as sd

config = get_yaml_config()

width = config["stable_diffusion"]["width"]
height = config["stable_diffusion"]["height"]
source_path = config["batch"]["source_path"]
dest_path = config["batch"]["output_path"]
ending_splice_video_path = config["batch"]["ending_splice_path"]


def create_cover(save_path, filename, directory_nickname=None):
    obj = {
        "prompt": "Cover image, shocking, eye-catching,",
        "negative_prompt": "nsfw,(low quality,normal quality,worst quality,jpeg artifacts),cropped,monochrome,lowres,low saturation,((watermark)),(white letters)"
    }
    cover = True
    if directory_nickname:
        dirname_path_ = os.path.dirname(save_path)
        dirname_path = os.path.dirname(dirname_path_)

        if os.path.exists(os.path.join(dirname_path, "cover.png")):
            cover = False
    if cover:
        obj["prompt"] += translate.main(filename)
        if directory_nickname:
            asyncio.run(sd().draw_picture(obj, "cover", dirname_path))
        else:
            asyncio.run(sd().draw_picture(obj, "cover", save_path))
    if directory_nickname:
        cover_path = os.path.join(dirname_path, "cover.png")
        out_path = os.path.join(save_path, "cover.png")
    else:
        cover_path = os.path.join(save_path, "cover.png")
        out_path = os.path.join(save_path, "out_cover.png")
    add_watermark(cover_path, out_path, f"《{filename}》")
    if not directory_nickname:
        os.replace(out_path, cover_path)
    return out_path if directory_nickname else cover_path


def merge_cover(save_path, filename, video_path, directory_nickname=None):
    cover_video = os.path.join(save_path, "temp_cover_video.mp4")
    cover_image = create_cover(save_path, filename, directory_nickname)
    # 将 PNG 图片转换为短视频片段
    subprocess.run([
        'ffmpeg', '-y', '-loop', '1', '-framerate', '25', '-i', cover_image,
        '-c:v', 'libx264', '-t', '0.04', '-pix_fmt', 'yuv420p',
        '-vf', f'scale={width}:{height}', cover_video
    ], check=True)

    output_video = os.path.join(save_path, "output.mp4")
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", cover_video,  # 第一个视频文件路径
        "-i", video_path,  # 第二个视频文件路径
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[outv]",  # 使用concat滤镜进行拼接
        "-map", "[outv]",  # 映射视频输出
        "-map", "1:a?",  # 映射音频输出
        output_video  # 输出文件路径
    ]
    subprocess.run(ffmpeg_command, check=True)
    # 删除临时的封面视频文件
    os.remove(cover_video)
    os.replace(output_video, video_path)


def merge_videos(secondary_video_path, output_video_path, name):
    main_video_path = os.path.join(output_video_path, f"{name}.mp4")
    final_path = os.path.join(output_video_path, f"{name}_final.mp4")
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", main_video_path,  # 第一个视频文件路径
        "-i", secondary_video_path,  # 第二个视频文件路径
        "-filter_complex",
        "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",  # 使用concat滤镜进行拼接
        "-map", "[outv]",  # 映射视频输出
        "-map", "[outa]",  # 映射音频输出
        final_path  # 输出文件路径
    ]
    subprocess.run(ffmpeg_command, check=True)

    # 清理临时文件
    os.replace(final_path, main_video_path)


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[36m'
    BRIGHT_BLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# 使用正则表达式从文件名中提取数字
def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    return None


def main(source_path, directory_nickname=None):
    txt_files = [f for f in os.listdir(source_path) if f.endswith('.txt')]

    sorted_files = sorted(txt_files, key=extract_number)

    for filename in sorted_files:
        file_path = os.path.join(source_path, filename)
        if os.path.isfile(file_path):
            name = filename.split(".")[0]
            store_path = os.path.join(dest_path, name)
            if directory_nickname:
                store_path = os.path.join(dest_path, directory_nickname, name)
            path = os.path.join(store_path, "participle")
            participle_path = os.path.join(path, f"{name}.txt")
            picture_save_path = os.path.join(store_path, "pictures")
            save_path = os.path.join(store_path, "video")
            asyncio.run(participle(file_path, path, participle_path))
            if classify in ["1", "2"]:
                asyncio.run(role(path, name))
                asyncio.run(generate_prompt(path, path, name))
                asyncio.run(new_draw_picture(path, name, picture_save_path))
            if classify in ["1", "3"]:
                asyncio.run(voice_srt(participle_path, path, file_path, name))
            if classify in ["1", "4"]:
                is_exists = vc().merge_video(picture_save_path, path, name, save_path)
                if ending_splice_video_path and not is_exists:
                    merge_videos(ending_splice_video_path, save_path, name)
                if not is_exists:
                    merge_cover(save_path, name, os.path.join(save_path, f"{name}.mp4"), directory_nickname)
                # 将原文移到新目录 并且名字加上已完成
                os.rename(file_path, os.path.join(store_path, f"{name}_已完成.txt"))


if __name__ == "__main__":

    # 使用定义好的颜色和样式来打印选项
    print(f"{Colors.HEADER}欢迎使用我们的视频处理工具{Colors.ENDC}")
    print(f"{Colors.OKGREEN}1: {Colors.BOLD}一键完成{Colors.ENDC}")
    print(f"{Colors.BRIGHT_BLUE}2: {Colors.BOLD}生成分词+图片{Colors.ENDC}")
    print(f"{Colors.OKGREEN}3: {Colors.BOLD}生成语音{Colors.ENDC}")
    print(f"{Colors.WARNING}4: {Colors.BOLD}已经检测过图片，直接合成视频{Colors.ENDC}")
    print(f"{Colors.HEADER}输入后回车，默认为1{Colors.ENDC}")
    classify = input(f"{Colors.OKCYAN}请输入要操作的类型：{Colors.ENDC}") or "1"

    entries = os.listdir(source_path)
    subdirectories = [
        entry for entry in entries
        if
        os.path.isdir(os.path.join(source_path, entry)) and not entry.startswith('.') and not entry.startswith('_')
    ]
    # 这里是所有source_path目录下的子目录，首先先
    for directory in subdirectories:
        main(os.path.join(source_path, directory), directory)
    main(source_path, None)
