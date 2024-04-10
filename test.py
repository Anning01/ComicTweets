import subprocess
import os

# 合并文件夹下所有MP3文件为一个音频文件
def merge_bgm(bgm_folder):
    with open('bgm_list.txt', 'w') as filelist:
        for mp3_file in os.listdir(bgm_folder):
            if mp3_file.endswith('.mp3'):
                filelist.write(f"file '{os.path.join(bgm_folder, mp3_file)}'\n")
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'bgm_list.txt', '-c', 'copy', 'merged_bgm.mp3'], check=True)
    os.remove('bgm_list.txt')

# 获取媒体文件长度
def get_media_length(file_path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path], stdout=subprocess.PIPE, text=True)
    return float(result.stdout)

# 循环BGM以匹配主音轨长度，然后与主音轨混合
def mix_main_and_bgm(main_audio, bgm_file, output_file, main_volume='0dB', bgm_volume='-20dB'):
    main_length = get_media_length(main_audio)
    bgm_length = get_media_length(bgm_file)

    # 计算BGM需要循环的次数
    loop_count = int(main_length // bgm_length) + 1 if bgm_length < main_length else 1

    # 如果需要，循环BGM
    if loop_count > 1:
        with open('looped_bgm_list.txt', 'w') as loop_file:
            for _ in range(loop_count):
                loop_file.write(f"file '{bgm_file}'\n")
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'looped_bgm_list.txt', '-c', 'copy', 'looped_bgm.mp3'], check=True)
        looped_bgm = 'looped_bgm.mp3'
        os.remove('looped_bgm_list.txt')
    else:
        looped_bgm = bgm_file

    # 转换循环后的BGM为单声道，采样率调整为24kHz
    subprocess.run(['ffmpeg', '-i', looped_bgm, '-ac', '1', '-ar', '24000', 'bgm_converted.mp3'], check=True)

    # 混合主音轨和已转换的BGM
    subprocess.run([
        'ffmpeg', '-i', main_audio, '-i', 'bgm_converted.mp3',
        '-filter_complex',
        f"[0:a]aformat=sample_rates=24000:channel_layouts=mono,volume={main_volume}[a0];[1:a]aformat=sample_rates=24000:channel_layouts=mono,volume={bgm_volume}[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
        '-map', '[aout]', '-ac', '1', '-ar', '24000', '-y', output_file
    ], check=True)

    # 清理临时文件
    os.remove('merged_bgm.mp3')
    os.remove('bgm_converted.mp3')
    if loop_count > 1:
        os.remove('looped_bgm.mp3')

# 使用示例
bgm_folder = 'bgm'  # 替换为你的BGM文件夹路径
main_audio = 'participle/残忍冷血大佬被傻妻抱怀里了第一章离婚/残忍冷血大佬被傻妻抱怀里了第一章离婚.mp3'  # 替换为你的主音轨文件路径
output_audio = 'audio.mp3'  # 替换为输出音频的路径

merge_bgm(bgm_folder)
mix_main_and_bgm(main_audio, 'merged_bgm.mp3', output_audio)
