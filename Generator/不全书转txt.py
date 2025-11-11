import os
import re
import argparse
import sys

# 尝试导入 BeautifulSoup，如果不存在则提示安装
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("错误: 未找到 BeautifulSoup 库。请使用 pip 安装它:")
    print("pip install beautifulsoup4")
    exit(1)
    

def transform_html_2_txt(base_path, output_path = None):
    """
    转换html文件为txt文件
    转换base_path目录下的所有html文件为txt文件
    转换后的txt文件与html文件在同一目录下，文件名相同，只是扩展名不同
    转换后的txt文件内容为html文件的文本内容，不包含html标签

    Args:
        base_path (str): HTML文件所在的基础目录路径
    """
    # 检查目录是否存在
    if not os.path.isdir(base_path):
        raise ValueError(f"目录不存在: {base_path}")

    if output_path is None:
        # 如果输出目录不存在，则输出路径默认与输入路径相同
        output_path = base_path
    
    # 遍历目录下所有HTML文件
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(('.html', '.htm')):
                html_path = os.path.join(root, file)
                # 计算输出文件的路径
                relative_path = os.path.relpath(root, base_path)
                txt_path = os.path.join(output_path, relative_path, os.path.splitext(file)[0] + '.txt')
                # 创建输出目录（如果不存在）
                os.makedirs(os.path.dirname(txt_path), exist_ok=True)

                # 读取并解析HTML内容
                try:
                    encodings = ['utf-8', 'gbk', 'latin-1']
                    content = None
                    
                    for encoding in encodings:
                        try:
                            with open(html_path, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    soup = BeautifulSoup(content, 'html.parser')

                    # 提取文本内容（保留原始HTML换行结构）
                    text_parts = []
                    for element in soup.descendants:
                        if element.name is None:
                            # 处理文本节点
                            if element:
                                text_parts.append(element.replace('\n',''))
                        elif element.name == 'br':
                            # 处理<br>标签为换行
                            text_parts.append('\n')
                        elif element.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol']:
                            # 块级元素前后添加空行
                            text_parts.append('\n\n')

                    # 合并内容并处理连续空行
                    text_content = ''
                    for i, t in enumerate(text_parts):
                        # 如果连续2个t都是英文，则判断他们之前有没有空格，没有则加一个
                        if i != 0 and re.match(r'^[a-zA-Z]+$', t) and re.match(r'^[a-zA-Z]+$', text_parts[i-1]):
                            if not re.search(r'[a-zA-Z]\s+[a-zA-Z]', t + text_parts[i-1]):
                                text_content += ' '
                        text_content += t
                    # 替换多个连续换行符为两个换行符（保留段落结构）
                    text_content = re.sub(r'\n+', '\n', text_content).strip()

                    # 清理开头的编码声明
                    if text_content.startswith('coding:'):
                        text_content = '\n'.join(text_content.split('\n')[1:])
                    
                    # 清理结尾的EndFragment
                    if text_content.endswith('EndFragment'):
                        text_content = text_content[:-len('EndFragment')]
                        
                    # 写入TXT文件
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)

                    print(f"转换完成: {html_path} -> {txt_path}")

                except Exception as e:
                    print(f"处理文件失败 {html_path}: {str(e)}")
                    
if __name__ == "__main__":
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 计算项目根目录的绝对路径 
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    parser = argparse.ArgumentParser()
    parser.add_argument("base_path", nargs="?", default=root_dir, help="不全书根目录")
    parser.add_argument("output_path", nargs="?", default=os.path.join(script_dir, "Generated/txt"), help="输出TXT文件的路径")
    args = parser.parse_args()
    transform_html_2_txt(args.base_path, args.output_path)