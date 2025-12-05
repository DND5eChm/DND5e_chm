#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将htm文件中的英文中的包裹的全角单引号替换为半角单引号
"""

import os
import re

def replace_fullwidth_quotes_in_english(file_path):
    """
    替换htm文件中英文内容中的全角引号为半角引号
    :param file_path: 文件路径
    """
    try:
        # 尝试使用UTF-8编码打开文件
        encoding = 'utf-8'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用GBK编码
            encoding = 'gbk'
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        # 正则表达式：匹配英文单词或字符前后的全角引号
        # 模式解释：
        # (?<![一-龥]) - 前面不是中文字符
        # [“”] - 匹配全角引号
        # (?![一-龥]) - 后面不是中文字符
        pattern = r'(?<![一-龥])[’](?![一-龥])'
        
        # 替换为半角引号
        modified_content = re.sub(pattern, '\'', content)
        
        # 只有当内容发生变化时才写入文件
        if modified_content != content:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(modified_content)
            print(f"已处理文件: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {e}")
        return False

def process_directory(directory):
    """
    遍历目录下所有htm文件并处理
    :param directory: 目录路径
    """
    total_files = 0
    processed_files = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.htm'):
                total_files += 1
                file_path = os.path.join(root, file)
                if replace_fullwidth_quotes_in_english(file_path):
                    processed_files += 1
    
    print(f"\n处理完成！")
    print(f"总文件数: {total_files}")
    print(f"已处理文件数: {processed_files}")

if __name__ == "__main__":
    # 从项目根目录开始处理
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    process_directory(project_root)