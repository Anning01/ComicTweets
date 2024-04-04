# ComicTweets
自动化构建漫画推文，使用stable diffusion来生成图片

# Installation and Running

## Windows 10/11 or Linux or macos

1. Install Python 3.8 or later from https://www.python.org/downloads/ or Install Conda https://www.anaconda.com/download
2. Install the required Python packages
   - - Run `pip install -r requirements.txt`
3. Run `python main.py`

Please make sure to install `ImageMagick` and  `FFmpeg` if you encounter any issues.

## ImageMagick Install

1. Download and install ImageMagick from https://www.imagemagick.org/script/download.php
2. Add ImageMagick to your PATH environment variable
3. Put magick.exe absolute path under the video.imagemagick_path of config.yaml under the project (macos or linux negligible)

## FFmpeg Install

1. Download and install FFmpeg from https://www.ffmpeg.org/
2.  Add FFmpeg to your PATH environment variable


# Introduction to use
Place the .txt file in the project root directory
Then copy the name of txt into the book name of config.yaml
running python main.py

# GPT
Supports API2D only
Type the key into the ForwardKey of chatgpt in config


# 下一步开发打算
1. 并发异步执行，现在都是同步执行，后面会让生产语音和生成图片的协程并行
2. 人物形象图，现在人物都是让GPT理解上下文的人物，形象可能会有一点变化，后面考虑使用 Reference 或者 ip-adapter 生成人物形象图参考。
3. moviepy 代码迁移到ffmpeg的原生命令，moviepy的最新版居然是2020年！！！ 已经没人更新了
4. 代码结构优化，现在代码写的很乱，需要优化
5. 新增ChatGPT 官方 API，因为没有key 只能使用国内的代理商，但是贵了1.5倍！！！