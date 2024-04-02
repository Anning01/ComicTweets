import json
import os
from api2d import Main


def write_to_json(data, filename):
    with open(filename, "a") as file:  # 使用 'a' 模式以追加模式打开文件
        if file.tell() == 0:  # 如果文件为空
            file.write("[")  # 在第一次写入数据时写入数组的起始括号
        else:
            file.write(",")  # 在非第一次写入数据时，先写入逗号分隔符

        json.dump(data, file)
        file.write("\n")  # 在每个 JSON 对象之后添加换行符，以便每个对象占用单独的行


def extract_str(text):
    xx = text["content"]

    xxx = xx.split("**Negative Prompt:**", 1)

    prompt = (
        xxx[0]
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
    )
    negative_prompt = (
        xxx[1]
        .replace("**Negative Prompt:**", "")
        .replace("**Prompt:**", "")
        .replace("\n", "")
    )

    return prompt, negative_prompt


def generate_prompt(path, save_path, name):

    with open(f"{path}/{name}.txt", "r", encoding="utf8") as file:
        # 初始化行数计数器
        line_number = 0
        lines = file.readlines()
        messages = []
        # 循环输出每一行内容
        prompt_json_save_path = os.path.join(save_path, f"{name}.json")

        for line in lines:
            line_number += 1
            text = f"第{line_number}段：" + line.strip()
            if line_number == 1:
                with open(f"{name}prompt.txt", "r", encoding="utf8") as f:
                    messages = [
                        {
                            "role": "system",
                            "content": f.read(),
                        }
                    ]
            result, message = Main().prompt_generation_chatgpt(text, messages)
            prompt, negative_prompt = extract_str(message)

            write_to_json(
                {"prompt": prompt, "negative_prompt": negative_prompt}, prompt_json_save_path
            )
            messages = result + [message]
        with open(prompt_json_save_path, "a") as f:
            f.write("]")


if __name__ == "__main__":
    generate_prompt()
