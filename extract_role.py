from collections import Counter

import jieba
import yaml

with open('config.yaml', 'r', encoding="utf-8") as file:
    config = yaml.safe_load(file)
min_length = config['potential']['min_length']
max_length = config['potential']['max_length']
top_n = config['potential']['top_n']


def extract_potential_names(text):

    # 使用 jieba 进行中文分词
    words = jieba.lcut(text)

    # 过滤出符合要求的词汇
    filtered_words = [word for word in words if min_length <= len(word) <= max_length]

    # 统计词频
    word_counts = Counter(filtered_words)

    # 选取频率最高的词汇
    top_names = [word for word, count in word_counts.most_common(top_n)]

    return top_names


if __name__ == "__main__":
    # 假设这是你的中文小说文本
    with open('./表白.txt', "r", encoding="utf8") as f:
        novel_text = f.read().replace("\n", "").replace("\r", "").replace("\r\n", "")

    # 提取文本中的潜在人名
    names = extract_potential_names(novel_text)

    print(names)
