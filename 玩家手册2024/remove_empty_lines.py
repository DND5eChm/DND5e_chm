import os
import re
from pathlib import Path

def remove_empty_lines(filepath):
    """删除文件中仅包含空白字符的行"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配仅包含空白字符的行及其后的换行符
    pattern = re.compile(r'^(\s*)$\n', re.MULTILINE)
    new_content = pattern.sub('', content)
    
    # 将连续两个以上的空格替换为单个空格
    new_content = re.sub(r' {2,}', ' ', new_content)
    new_content = re.sub(r' <', '<', new_content)
    new_content = re.sub(r'< ', '<', new_content)
    new_content = re.sub(r' >', '>', new_content)
    new_content = re.sub(r'> ', '>', new_content)
    new_content = re.sub(r'\n<p></p>', '', new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def process_directory(directory):
    """递归处理目录下所有.htm文件"""
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.htm'):
                filepath = os.path.join(root, file)
                if remove_empty_lines(filepath):
                    print(f'处理了文件: {filepath}')
                    count += 1
    print(f'共处理了 {count} 个文件')

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    process_directory(current_dir)
