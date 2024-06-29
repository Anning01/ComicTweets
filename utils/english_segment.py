#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @author:anning
# @email:anningforchina@gmail.com
# @time:2024/06/13 20:55
# @file:english_segment.py
import nltk


def split_text_into_paragraphs(text):
    # 将文本分割成段落
    paragraphs = text.split('\n\n')
    return paragraphs


def split_paragraphs_into_sentences(paragraphs):

    sentences = []
    for paragraph in paragraphs:
        # 将段落分割成句子
        sentences.extend(nltk.sent_tokenize(paragraph))
    return sentences


def split_spain_paragraphs_into_sentences(paragraphs):

    sentences = []
    for paragraph in paragraphs:
        # 使用西班牙语的punkt分词器
        sentences.extend(nltk.sent_tokenize(paragraph, language='spanish'))
    return sentences


def main(file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    paragraphs = split_text_into_paragraphs(text)
    sentences = split_paragraphs_into_sentences(paragraphs)

    # 输出分段后的内容
    for i, sentence in enumerate(sentences):
        print(f'Sentence {i + 1}: {sentence}')
        # 逐行写入文件
        with open('output.txt', 'a', encoding='utf-8') as file:
            file.write(sentence + '\n')


if __name__ == '__main__':
    main('./小说目录/e.txt')