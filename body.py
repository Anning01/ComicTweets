import streamlit as st
import subprocess
import os
import json
from streamlit_option_menu import option_menu
import time
import shutil
from pathlib import Path
import asyncio
import os.path
import re
import subprocess
from PIL import Image
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
from mass_production import create_cover, merge_cover, merge_videos, extract_number
from ruamel.yaml import YAML
config = get_yaml_config()


source_path = config["batch"]["source_path"]
dest_path = config["batch"]["output_path"]
ending_splice_video_path = config["batch"]["ending_splice_path"]
voice_select = config["audio"]["role"]

def get_first_txt_filename(directory,num):
    # 遍历目录中的文件和子目录
    for filename in os.listdir(directory):
        # 检查文件是否以.txt结尾
        if filename.endswith('.txt'):
            # 使用split()方法移除扩展名，并返回文件名部分
            return filename.rsplit('.', 1)[num]
    # 如果没有找到.txt文件，则返回None
    return None


def read_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

# 保存txt文件内容
def save_txt_file(file_path, new_content, index):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()  # 确保这一行在if语句之前

    # 确保index在有效范围内
    if index < 1 or index > len(lines):
        raise IndexError("Index is out of the valid range.")

    # 更新指定行的内容
    lines[index - 1] = new_content.strip() + '\n'  # 索引从0开始，所以要减1

    # 将更新后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

# 读取json文件内容
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 保存json文件内容
def save_json_file(file_path, json_data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)

# 删除图片文件
def delete_picture(picture_number):
    picture_path = os.path.join(picture_folder_path, f"{picture_number}.png")
    if os.path.exists(picture_path):
        os.remove(picture_path)
def show_full_image(image_path):
    img = Image.open(image_path)
    st.image(img, caption='Full Image', use_column_width=True)


def show_images(folder_path):
    images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and any(
        f.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif'])]
    for i, image_name in enumerate(images):
        image_path = os.path.join(folder_path, image_name)
        st.image(Image.open(image_path))

        # 修改文件名
        new_name = st.text_input(f'New name for {image_name}:')
        if st.button(f'Rename {image_name}'):
            if new_name and new_name != image_name:
                new_path = os.path.join(folder_path, new_name)
                os.rename(image_path, new_path)
                st.success(f'{image_name} renamed to {new_name}')

        # 删除图片
        if st.button(f'Delete {image_name}'):
            try:
                # 将图片移动到回收站（需要Windows系统）
                # 在其他操作系统上，您可能需要使用其他方法来实现删除到回收站的功能
                recycle_bin = Path.home() / '.Trash'
                if not os.path.exists(recycle_bin):
                    os.makedirs(recycle_bin)
                shutil.move(image_path, recycle_bin / image_name)
                st.success(f'{image_name} moved to recycle bin')
            except Exception as e:
                st.error(f'Error deleting {image_name}: {e}')

        st.markdown('---')
import re

def read_yaml(yaml_file_path):
    yaml = YAML()
    with open(yaml_file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)

# 写入修改后的YAML文件内容
def write_yaml(data, yaml_file_path):
    yaml = YAML()
    with open(yaml_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)

def split_text_by_chapter(text):
    # 正则表达式匹配章节标题
    chapter_pattern = re.compile(r'第(\d+)章')

    # 找到所有章节标题的位置
    chapter_positions = [m.start() for m in chapter_pattern.finditer(text)]

    # 如果没有找到章节标题，则按照每2600个字符分割
    if not chapter_positions:
        max_chars = 2600
        split_texts = []
        start = 0
        while start < len(text):
            end = text.find('。', start + max_chars)
            if end == -1:
                end = len(text)
            split_texts.append(text[start:end].strip())
            start = end + 1
        return split_texts

    # 如果有章节标题，按照章节分割，并确保章节标题和内容合并
    split_texts = []
    start = 0
    for pos in chapter_positions:
        # 提取当前章节的内容（包括章节标题）
        chapter_content = text[start:pos]
        if chapter_content.strip():
            # 如果章节内容不为空，则添加到结果列表中
            split_texts.append(chapter_content)

        # 移动指针到章节标题的末尾
        start = pos + len("第X章")  # 假设章节标题的格式是"第X章"，X是数字

    # 添加最后一个章节之后的内容（如果有）
    if start < len(text):
        split_texts.append(text[start:].strip())

    return split_texts


def save_split_texts(original_filename, split_texts):
    base_filename = original_filename.rsplit('.', 1)[0]

    for i, part in enumerate(split_texts, start=1):
        # 确保文件名不会太长
        filename = f"{base_filename}_{i:03d}.txt"
        with open(filename, 'w', encoding='utf-8') as new_file:
            new_file.write(part)

    print(f"Processed {original_filename} into {len(split_texts)} files.")
def selected_file(folder_path):
    txt_files = {file: os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.txt')}

    # 将文件名列表转换为简单的列表
    txt_file_list = list(txt_files.keys())

    # 创建下拉框供用户选择文件
    selected_file_name = st.selectbox('选择一个TXT文件:', txt_file_list)

    # 根据用户选择显示文件内容
    if selected_file_name:
        selected_file_path = txt_files[selected_file_name]
        with open(selected_file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        st.write(f"文件名: {selected_file_name}")

def role_co(source_path, directory_nickname=None):
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
            asyncio.run(role(path, name))




# 定义网页标题
st.set_page_config(page_title='困困漫剪', layout='wide')
# 定义边栏导航
with st.sidebar:
    choose = option_menu('首页', ['上传小说', '预设人物', '编辑提示词与修改图片', '合成视频', '设置'],
                         icons=['house', 'book-half', 'book-half', 'book-half', 'book-half'])

# 创建允许客户上传小说的文本。


if choose == '上传小说':
    st.title("欢迎来到坤坤漫剪")
    uploaded_file = st.file_uploader('请在这里上传您的小说，暂时只支持TXT格式')
    path_directory = "novel_in_here"
    if uploaded_file is not None:
        # 获取上传文件的名称
        filename = uploaded_file.name

        # 检查文件是否是.txt格式
        if filename.endswith('.txt'):
            file_path = os.path.join(path_directory, filename)
            # 保存文件到指定目录
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())

            st.success('文件已成功保存至 {}'.format(path_directory))
        else:
            st.error('请上传一个.txt格式的文件。')
        uploaded_file_path = "novel_in_here/{}".format(filename)
        text_content = ''
        if uploaded_file is not None:
            with open(uploaded_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        modified_text = st.text_area('请在这里修改文本内容', text_content)
        if st.button('保存修改后的内容'):
            with open(uploaded_file_path, 'w', encoding='utf-8') as f:
                f.write(modified_text)
            st.success('修改后的内容已成功保存')
    if st.button("切分文本"):

        with open(uploaded_file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        split_texts = split_text_by_chapter(text)
        save_split_texts(uploaded_file_path, split_texts)
        os.remove(uploaded_file_path)
    txt_files = {file: os.path.join(path_directory , file) for file in os.listdir(path_directory) if file.endswith('.txt')}

    # 将文件名列表转换为简单的列表
    txt_file_list = list(txt_files.keys())

    # 创建下拉框供用户选择文件
    selected_file_name = st.selectbox('此处可以浏览目录下所有的文本:', txt_file_list)

    # 根据用户选择显示文件内容
    if selected_file_name:
        selected_file_path = txt_files[selected_file_name]
        with open(selected_file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        st.write(f"文件名: {selected_file_name}")
    st.write("请首先完成固定人物")
    if st.button('点此固定人物,这将处理目录下所有的文本！'):
        role_co(path_directory, directory_nickname=None)
    if st.button('点击此处可以执行直接运行的脚本！'):
        batch_file_path = '批量处理文本.bat'
        # 使用subprocess运行脚本
        try:
            result = subprocess.run(batch_file_path, shell=True)
            st.success('脚本执行成功！')
            st.write('脚本输出：')
            st.write(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error('脚本执行出错！')
            st.write('错误信息：')
            st.write(e.stderr)
    st.write("下面是您固定好的人物，请根据预设人物页面自行增加删改人物，注意图片名要与预设人物页面名字对应")
    directory_path = "novel_in_here"

    name = os.path.splitext(selected_file_name)[0]
    json_file = f'out_file/{name}/participle/role.json'
    json_data = read_json_file(json_file)
    data = read_json_file(json_file)
    json_file_dir = f'out_file/{name}/participle'
    json_filename = "role.json"
    json_file_path = os.path.join(json_file_dir, json_filename)
    # 使用 st.text_area 显示 JSON 字符串
    if 'edited_json_data' not in st.session_state:
        st.session_state.edited_json_data = json_data

    # 创建一个按钮来触发编辑 JSON 数据的操作



        # 展示现有数据
    for i, item in enumerate(data):
        st.write(f"### 角色姓名: {item['name']}")
        st.write(f"### 角色图片: {item['role']}")
        new_name = st.text_input("新的角色姓名:", value=item['name'], key=f"name_input_{i}")
        new_role = st.text_input("新的角色图片名称:", value=item['role'], key=f"role_input_{i}")
        if json_data != st.session_state.edited_json_data:
            save_json_file(json_file_path, st.session_state.edited_json_data)
            st.success('数据已保存到文件！')
            # 重新读取数据以确保下次比较是准确的
            json_data = st.session_state.edited_json_data.copy
        if new_name != item['name']:
            st.session_state.edited_json_data[i]['name'] = new_name
            save_json_file(json_file, data)
        if new_role != item['role']:
            st.session_state.edited_json_data[i]['role'] = new_role
            save_json_file(json_file, data)
            # 弹出输入框供用户编辑

        # 删除按钮逻辑
        if st.button(f"删除角色 {i + 1}", key=f"delete_button_{i}"):
            del st.session_state.edited_json_data[i]  # 删除 session_state 中的项
            del data[i]  # 删除 data 中的项
            save_json_file(json_file, data)  # 保存更改
            st.success('角色信息已删除！')
            break  # 停止循环


    with st.form("add_role_form"):
        new_name = st.text_input("新的角色姓名:")
        new_role = st.text_input("新的角色图片名称:")
        
        # 当用户点击提交按钮时，执行以下代码
        if st.form_submit_button("添加新角色"):
            # 用户提交表单后执行的逻辑
            if new_name and new_role:
                data.append({"name": new_name, "role": new_role})
                st.session_state.edited_json_data.append({"name": new_name, "role": new_role})
                st.success('新角色已添加！')
                save_json_file(json_file_path, data)  # 保存数据到文件

            # 重置输入框的值
            new_name = ""
            new_role = ""



    # 检查数据是否需要保存
    if json_data != st.session_state.edited_json_data:
        save_json_file(json_file_path, st.session_state.edited_json_data)
        st.success('数据已保存到文件！')
        json_data = st.session_state.edited_json_data.copy


elif choose == '预设人物':
    st.title("这里是固定人物的图片，请尽量选择空白背景的图片")
    # 设置图片文件夹路径
    image_folder = 'roles'

    # 确保图片文件夹存在
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "gif"])
    if uploaded_file is not None:
        with open(os.path.join(image_folder, uploaded_file.name), 'wb') as f:
            f.write(uploaded_file.read())
        st.success(f'{uploaded_file.name} 上传成功')

    # 显示图片

    show_images(image_folder)



elif choose =='编辑提示词与修改图片':
    st.title("在此浏览生成的提示词以及修改图片")
    directory_path = "novel_in_here"
    txt_files = {file: os.path.join(directory_path , file) for file in os.listdir(directory_path) if file.endswith('.txt')}

    # 将文件名列表转换为简单的列表
    txt_file_list = list(txt_files.keys())
    if st.button('点此生成提示词和图片,注意这将处理目录下所有的文本！'):
        directory_nickname=None
        txt_file_list = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
        sorted_files = sorted(txt_file_list, key=extract_number)
        for filename in sorted_files:
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                name = filename.split(".")[0]
                store_path = os.path.join(dest_path, name)
                if directory_nickname:
                    store_path = os.path.join(dest_path, directory_nickname, name)
                path = os.path.join(store_path, "participle")
                participle_path = os.path.join(path, f"{name}.txt")
                picture_save_path = os.path.join(store_path, "pictures")
                save_path = os.path.join(store_path, "video")
                asyncio.run(generate_prompt(path, path, name))
                asyncio.run(new_draw_picture(path, name, picture_save_path))


    # 创建下拉框供用户选择文件

    selected_file_name = st.selectbox('选择一个TXT文件:', txt_files)
    selected_file_path = txt_files[selected_file_name]

    # 根据用户选择显示文件内容
    if selected_file_name:
        with open(selected_file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        st.write(f"文件名: {selected_file_name}")

    name = os.path.splitext(selected_file_name)[0]
    if not os.path.exists(f'out_file/{name}/participle/{name}.json'):
        st.write("请先完成提示词和图片的生成")
    txt_file_path = f'out_file/{name}/participle/{name}.txt'
    json_file_path = f'out_file/{name}/participle/{name}.json'
    picture_folder_path = f'out_file/{name}/pictures'



    # 读取txt文件和json文件内容
    txt_lines = read_txt_file(txt_file_path)
    json_data = read_json_file(json_file_path)

    # 遍历txt文件的每一行
    for i, line in enumerate(txt_lines, start=1):
        cols = st.columns([3, 8, 2, 1])  # 创建4列，可以根据需要调整比例
        with cols[0]:
            # 展示并编辑文本内容
            edited_line = st.text_area(f"Line {i}:", value=line.strip(), key=f'txt_{i}')
            if edited_line:  # 确保文本框中有内容
                save_txt_file(txt_file_path, edited_line, i)

        with cols[1]:
            # 展示并编辑JSON键值对
            json_prompt = json_data[i - 1].get('prompt', "")
            edited_prompt = st.text_area("JSON Prompt:", value=json_prompt, key=f'json_{i}')
            if edited_prompt != json_prompt:
                json_data[i - 1]['prompt'] = edited_prompt
                save_json_file(json_file_path, json_data)

        with cols[2]:
            # 展示图片并提供删除功能
            picture_name = f"{i}.png"
            picture_path = os.path.join(picture_folder_path, picture_name)
            if os.path.exists(picture_path):
                img = Image.open(picture_path)
                img.thumbnail((300, 300))  # 调整图片大小
                st.image(img, caption='Thumbnail', use_column_width=False)

                # 创建一个按钮，点击时展示大图
                show_full_button = st.button(f"Show Full Image {i}")

                # 判断按钮是否被点击
                if show_full_button:
                    st.image(picture_path, use_column_width=True)
                    if st.button("关闭"):
                        st.expander("Full Image", expanded=False)

        with cols[3]:
            delete_button = st.button('Delete', key=f'delete_{i}')
            if delete_button:
                delete_picture(i)
                st.experimental_rerun()



elif choose =='合成视频':
    st.title("选择描述人的语音模型和bgm")
    st.write("  推荐 zh-CN-YunxiNeural 男  zh-CN-XiaoyiNeural  一般  女  zh-CN-XiaoxiaoNeural 最好  女")
    source_path = "novel_in_here"
    file_path = 'roles_voice.txt'

    # 确保文件存在
    if os.path.isfile(file_path):
        # 读取文件内容到列表中，假设每行一个选项
        options = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                option = line.strip()  # 去除每行首尾的空白字符
                if option:  # 如果行不为空，则添加到选项列表
                    options.append(option)

        # 设置默认值
        default_option = voice_select
        # 如果默认值在选项列表中，则使用它，否则使用列表中的第一个选项
        default_index = options.index(default_option) if default_option in options else 0

        # 创建下拉框
        selected_option = st.selectbox(
            '请选择一个角色声音：',
            options,
            index=default_index
        )

        # 显示选中的选项
        st.write(f'你选择的角色声音是：{selected_option}')

        config_file_path = 'config.yaml'
        yaml = YAML()
        # 读取并解析YAML配置文件
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config = yaml.load(file)

        # 直接修改'audio'下的'role'值
        config['audio']['role'] = selected_option

        if st.button("保存"):
            # 写回更新后的内容到原始文件
            with open(config_file_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file)
            st.success("保存成功")

    else:
        st.error(f'文件不存在.')
    bgm_data_folder = 'bgm_data'  # 替换为bgm_data文件夹的实际路径
    bgm_folder = 'bgm'  # 替换为bgm文件夹的实际路径

    # 读取bgm_data文件夹下的所有mp3文件
    mp3_files = [f for f in os.listdir(bgm_data_folder) if f.endswith('.mp3')]
    mp3_file = [f for f in os.listdir(bgm_folder) if f.endswith('.mp3')]

    uploaded_file = st.file_uploader("此处可以上传MP3文件", type=["mp3"])

    # 如果用户上传了文件
    if uploaded_file is not None:
        # 获取文件名
        file_name = uploaded_file.name
        # 获取文件的二进制内容
        file_contents = uploaded_file.read()

        # 保存文件到bgm_data文件夹
        save_path = os.path.join(bgm_data_folder, file_name)
        with open(save_path, 'wb') as f:
            f.write(file_contents)

        st.write(f'文件已上传并保存为：{save_path}')
        st.success(f'{file_name} 已保存到 {bgm_data_folder}')
    # 创建下拉框
    selected_mp3 = st.selectbox('从库中选择一个MP3文件:', mp3_files,key="one_bgm")
    st.write('注意，使用单曲BGM，将会清空bgm文件夹下的所有mp3文件。')
    if st.button("从库中永久删除此bgm"):
        os.remove(os.path.join(bgm_data_folder, selected_mp3))
        st.success("删除成功")
    if st.button("使用单曲BGM"):
        # 清空bgm文件夹下的mp3文件
        for file_name in os.listdir(bgm_folder):
            if file_name.endswith('.mp3'):
                os.remove(os.path.join(bgm_folder, file_name))
        # 复制用户选择的mp3文件到bgm文件夹
        shutil.copy(os.path.join(bgm_data_folder, selected_mp3), bgm_folder)
        st.success(f'已成功选择bgm: {selected_mp3}')
    if st.button("使用多曲BGM循环，点击添加库中的bgm"):
        shutil.copy(os.path.join(bgm_data_folder, selected_mp3), bgm_folder)
        st.success(f'已成功添加bgm: {selected_mp3}')

    selected_mp3 = st.selectbox('目前正在使用的bgm有:', mp3_file,key="more_bgm")

    if st.button("点此完成视频的合成"):
        st.write("请耐心等待完成，可以从操作台查看情况")
        directory_nickname = None
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
                asyncio.run(role(path, name))
                asyncio.run(generate_prompt(path, path, name))
                asyncio.run(new_draw_picture(path, name, picture_save_path))
                asyncio.run(voice_srt(participle_path, path, file_path, name))
                is_exists = vc().merge_video(picture_save_path, path, name, save_path)
                if bool(ending_splice_video_path) and not is_exists:
                    merge_videos(ending_splice_video_path, save_path, name)
                if not is_exists:
                    merge_cover(save_path, name, os.path.join(save_path, f"{name}.mp4"), directory_nickname)
                # 将原文移到新目录 并且名字加上已完成
                os.rename(file_path, os.path.join(store_path, f"{name}_已完成.txt"))
                st.success("恭喜已完成所有任务")

elif choose == '设置':
    st.write("其他到config.yaml里设置吧")
    yaml_file_path = 'config.yaml'
        # 初始化数据
    config_data = read_yaml(yaml_file_path)
    st.write('当前配置的role:', config.get('stable_diffusion', {}).get('lora', '未设置'))

    # 创建文本输入框允许用户修改数据
    st.write('这里可以添加lora和全体需要的关键词比如风格动漫风格animeartstyle，写实风格realistic style')

    # 假设我们有一个嵌套的字典结构
    role_input = st.text_input('添加lora:', value=config_data.get('stable_diffusion', {}).get('lora', ))

    # 当用户点击"保存"按钮时
    if st.button('保存修改'):
        # 更新config_data字典
        config_data.setdefault('stable_diffusion', {})['lora'] = role_input
        
        # 将修改后的数据写回YAML文件
        write_yaml(config_data, yaml_file_path)
        
        # 给用户反馈
        st.write('YAML文件已更新!')
    if st.button('显示当前配置'):
    # 显示当前配置
        st.write(config_data)


def main():
    st.write('感谢使用')
if __name__ == '__main__':
    main()







# 运行Streamlit应用
st.markdown("这是一个由Streamlit创建的前端页面。")
