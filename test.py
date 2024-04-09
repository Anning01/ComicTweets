import random
import subprocess
import os


# def create_animated_segment(image_path, duration, output_path, index):
#     # 放大
#     cmd = [
#         "ffmpeg",
#         "-y",  # Overwrite output files without asking
#         "-r", "25",  # Frame rate
#         "-loop", "1",  # Loop input image
#         "-t", str(duration),  # Duration of the output video segment
#         "-i", image_path,  # Input image
#         "-filter_complex", "scale=-2:ih*10,zoompan=z='zoom+0.001':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25*"+str(duration)+":s=720x1280",  # Filter for zoom effect
#         "-vframes", str(int(25 * duration)),  # Number of frames in the output video
#         "-pix_fmt", "yuv420p",  # Pixel format for compatibility
#         "-c:v", "libx264",  # Video codec
#         f"{output_path}/animated_segment_{index}.mp4"  # Output path
#     ]
#     subprocess.run(cmd, check=True)

def create_animated_segment(image_path, duration, output_path, index, multiple, action):
    initial_zoom = 1.0
    zoom_steps = (multiple - initial_zoom) / (25 * duration)
    print(zoom_steps)
    # 取余后三位
    # zoom_steps = round(zoom_steps, 3)
    if action == "shrink":
        scale = f"scale=-2:ih*10,zoompan=z='if(lte(zoom,{initial_zoom}),{multiple},max(zoom-{zoom_steps},1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25*" + str(duration) + ":s=720x1280"
    else:
        scale = f"scale=-2:ih*10,zoompan=z='min(zoom+{zoom_steps},{multiple})*if(gte(zoom,1),1,0)+if(lt(zoom,1),1,0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25*{duration}:s=720x1280"
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出文件
        "-r", "25",  # 帧率
        "-loop", "1",  # 循环输入图像
        "-t", str(duration),  # 输出视频片段的持续时间
        "-i", image_path,  # 输入图像
        "-filter_complex", scale,
        "-vframes", str(int(25 * duration)),
        "-c:v", "libx264",  # 视频编解码器
        "-pix_fmt", "yuv420p",  # 像素格式
        f"{output_path}/animated_segment_{index}.mp4"  # 输出路径
    ]
    subprocess.run(cmd, check=True)

def concat_videos(video_list, audio_path, output_video):
    with open("temp_list.txt", "w") as f:
        for video in video_list:
            f.write(f"file '{video}'\n")

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output files without asking
        "-f", "concat",
        "-safe", "0",
        "-i", "temp_list.txt",
        "-i", audio_path,
        "-vsync", "cfr",
        "-pix_fmt", "yuv420p",
        output_video
    ]
    subprocess.run(cmd, check=True)


def disposable_synthesis(picture_path_list, durations, audio_path, save_path, name):
    os.makedirs(save_path, exist_ok=True)

    video_list = []
    animations = ["shrink", "magnify"]
    for index, (image_path, duration) in enumerate(zip(picture_path_list, durations)):
        output_path = f"{save_path}/animated_segment_{index}.mp4"
        selected_animation = random.choice(animations)
        create_animated_segment(image_path, duration, save_path, index, 1.3, selected_animation)
        video_list.append(output_path)

    final_output = os.path.join(save_path, f"{name}.mp4")
    concat_videos(video_list, audio_path, final_output)

    # Optionally, remove temporary files
    for video in video_list:
        os.remove(video)
    os.remove("temp_list.txt")


# Example usage
picture_path_list = ["images/斗破苍穹/1.png", "images/斗破苍穹/2.png", "images/斗破苍穹/3.png", "images/斗破苍穹/4.png",
                     "images/斗破苍穹/5.png", "images/斗破苍穹/6.png", "images/斗破苍穹/7.png", "images/斗破苍穹/8.png",
                     "images/斗破苍穹/9.png", "images/斗破苍穹/10.png", "images/斗破苍穹/11.png",
                     "images/斗破苍穹/12.png",
                     "images/斗破苍穹/13.png"]
original_durations = ['0:00:06,018', '0:00:05,455', '0:00:04,223', '0:00:04,259', '0:00:04,447', '0:00:04,375',
                      '0:00:04,893', '0:00:04,901', '0:00:05,474', '0:00:06,339', '0:00:05,321', '0:00:07,215']


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


durations = [convert_time_string(duration) for duration in original_durations]
audio_path = "./participle/斗破苍穹/斗破苍穹.mp3"
save_path = "./"
name = "斗破苍穹"

disposable_synthesis(picture_path_list, durations, audio_path, save_path, name)
