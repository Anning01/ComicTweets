from io import StringIO
import os
import subprocess
import streamlit as st
from load_config import edit_yaml_config, get_yaml_config
from mass_production import main
from contextlib import redirect_stdout
from PIL import Image  

config = get_yaml_config()
source_path = config["batch"]["source_path"]
output_path = config["batch"]["output_path"]
ending_splice_path = config["batch"]["ending_splice_path"]
ForwardKey = config["chatgpt"]["ForwardKey"]
chat_url = config["chatgpt"]["url"]
model = config["chatgpt"]["model"]
access_key_id = config["potential"]["access_key_id"]
access_key_secret = config["potential"]["access_key_secret"]
ROLES_DIR = "roles"

def processing():
    st.title("批量处理")
    st.header("欢迎使用我们的视频处理工具")
    
    st.write("选择操作类型:")
    options = {
        "一键完成": "1",
        "生成分词+图片": "2",
        "生成语音": "3",
        "已经检测过图片，直接合成视频": "4",
        "先固定角色": "5"
    }
    
    # 使用 selectbox 进行类型选择
    classify = st.selectbox("请选择操作类型:", list(options.keys()), index=0)
    classify_value = options[classify]

    st.write(f"你选择的操作类型是：{classify}")

    st.write("输出路径:", output_path)


    # 创建一个占位符用于显示终端输出信息
    output_placeholder = st.empty()
    output_buffer = StringIO()

    
    # 批量处理按钮
    if st.button("开始批量处理"):
        entries = os.listdir(source_path)
        subdirectories = [
            entry for entry in entries
            if os.path.isdir(os.path.join(source_path, entry)) and not entry.startswith('.') and not entry.startswith('_')
        ]

        # 显示处理进度
        with st.spinner("正在处理..."):
            total_tasks = len(subdirectories) + 1  # 包括 source_path 的处理
            progress_bar = st.progress(0)
            for i, directory in enumerate(subdirectories):
                with redirect_stdout(output_buffer):
                    print(f"Processing directory: {directory}")
                    main(os.path.join(source_path, directory), directory)
                output_placeholder.text(output_buffer.getvalue())
                progress_bar.progress((i + 1) / total_tasks)
            with redirect_stdout(output_buffer):
                main(source_path, classify_value, None, output_path)
            output_placeholder.text(output_buffer.getvalue())
            progress_bar.progress(1.0)
        st.toast('处理完成！', icon='😍')
        subprocess.Popen(f'explorer "{output_path}"')

# 加载roles目录下的所有图片和昵称  
def load_role_images():  
    images = []  
    if os.path.exists(ROLES_DIR):  
        for filename in os.listdir(ROLES_DIR):  
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):  
                image_path = os.path.join(ROLES_DIR, filename)  
                # 假设昵称和文件名（不带扩展名）相同  
                nickname = os.path.splitext(filename)[0]  
                images.append((nickname, image_path))  
    return images  
  
def cycle_values(values):  
    """  
    Generate values from the given list in a circular fashion.  
  
    Args:  
        values (list): List of values to cycle through.  
  
    Returns:  
        Generator: Yields the next value in the cycle.  
    """  
    index = 0  
    while True:  
        yield values[index]  
        index = (index + 1) % len(values)  # Increment index and wrap around if necessary  
  

def roles():
    st.title("角色管理")
    
    # 上传新图片  
    uploaded_file = st.file_uploader("上传新图片到roles目录", type=["png", "jpg", "jpeg"])  
    if uploaded_file is not None:  
        # 保存图片到roles目录  
        filename = uploaded_file.name  
        new_filename = os.path.join(ROLES_DIR, filename)  
        with open(new_filename, 'wb') as f:  
            f.write(uploaded_file.getbuffer())  
        # 假设昵称和文件名（不带扩展名）相同  
        nickname = os.path.splitext(filename)[0]  
    
    # 显示所有图片和昵称 
    cycle = cycle_values(st.columns(3))  
    for nickname, image_path in load_role_images():
        instance = next(cycle)
        instance.write(f"昵称: {nickname}")  
        # 对于每个角色，显示修改昵称和删除图片的按钮  
        instance.image(Image.open(image_path))  
    

def configuration_information():
    st.title("配置信息")

    def save_config():
        config["batch"]["source_path"] = source_path_
        config["batch"]["output_path"] = output_path_
        config["batch"]["ending_splice_path"] = ending_splice_path_
        config["chatgpt"]["ForwardKey"] = ForwardKey_
        config["chatgpt"]["url"] = url_
        config["chatgpt"]["model"] = model_
        config["potential"]["access_key_id"] = access_key_id_
        config["potential"]["access_key_secret"] = access_key_secret_
        edit_yaml_config(config)
        st.toast('配置已更新', icon='😍')

    source_path_ = st.text_input("小说目录", source_path, help="请复制小说目录绝对路径或相对路径")
    output_path_ = st.text_input("输出目录", output_path, help="生产后视频的保存路径")
    ending_splice_path_ = st.text_input("视频尾部拼接", ending_splice_path, help="统一拼接尾部视频")
    ForwardKey_ = st.text_input("openai key, 支持国内代理，以及本地LLM大模型", ForwardKey, help="openai key, 支持国内代理，以及本地LLM大模型")
    url_ = st.text_input("openai url 代理或者本地需要填", chat_url, help="openai url，代理或者本地需要填")
    model_ = st.text_input("openai model 代理或者本地需要填", model, help="openai model，代理或者本地需要填")
    access_key_id_ = st.text_input("阿里云翻译access_key_id", access_key_id, help="阿里云access_key_id")
    access_key_secret_ = st.text_input("阿里云翻译access_key_secret", access_key_secret, help="阿里云access_key_secret")

    st.button("保存配置", on_click=save_config, use_container_width=True)



if __name__ == "__main__":
    st.sidebar.title("Apps")

    st.sidebar.write("Select an app:")
    if st.sidebar.button("配置信息", use_container_width=True):
        st.session_state.page = '配置'
    if st.sidebar.button("批量处理", use_container_width=True):
        st.session_state.page = '批量处理'
    if st.sidebar.button("角色管理", use_container_width=True):
        st.session_state.page = '角色管理'

    # 页面显示逻辑
    if 'page' in st.session_state:
        if st.session_state.page == '配置':
            configuration_information()
        elif st.session_state.page == '批量处理':
            processing()
        elif st.session_state.page == '角色管理':
            roles()
    else:
        st.session_state.page = '配置'
        configuration_information()