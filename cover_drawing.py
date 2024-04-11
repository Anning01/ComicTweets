#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/04/11 15:02
# @file:cover_drawing.py
from PIL import Image, ImageDraw, ImageFont


def add_watermark(image_path, output_path, text, font_path="simhei.ttf", font_color=(255, 165, 0),
                  margin_percentage=0.1):
    # 打开图片
    image = Image.open(image_path).convert("RGBA")
    image_width, image_height = image.size

    # 创建ImageDraw对象
    draw = ImageDraw.Draw(image)

    # 通过图片宽度和预定的边距百分比动态计算最大允许的文字宽度
    max_text_width = image_width * (1 - 2 * margin_percentage)

    # 初始化字体大小
    font_size = 1
    font = ImageFont.truetype(font_path, font_size)
    text_width, text_height = draw.textsize(text, font=font)

    # 动态调整字体大小，直到文字宽度接近最大允许宽度
    while text_width < max_text_width and text_height < image_height:
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)

    # 为了避免超出最大宽度，最后减小一点字体大小
    font_size -= 1
    font = ImageFont.truetype(font_path, font_size)

    # 计算文字位置以居中显示
    position = ((image_width - text_width) / 2, (image_height - text_height) / 2)

    # 绘制文字阴影或边线
    shadow_offset = 2
    for x_offset in range(-shadow_offset, shadow_offset + 1):
        for y_offset in range(-shadow_offset, shadow_offset + 1):
            draw.text((position[0] + x_offset, position[1] + y_offset), text, fill=(0, 0, 0), font=font)

    # 在阴影或边线之上绘制原始颜色的文字
    draw.text(position, text, fill=font_color, font=font)

    # 如果输出格式为JPG，需要将图像转换为RGB模式
    if output_path.endswith(".jpg") or output_path.endswith(".jpeg"):
        image = image.convert("RGB")

    # 保存图片
    image.save(output_path)


if __name__ == "__main__":
    # 使用示例
    add_watermark(
        image_path="image1.png",  # 图片路径
        output_path="output_image.png",  # 输出图片路径
        text="《回到古代从种田开始1》",  # 水印文字
        font_path="simhei.ttf",  # 字体路径，确保这个路径在你的系统上是有效的
        font_color=(255, 165, 0)  # 橙色字体
    )
