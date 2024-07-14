import os
import chardet

# def convert_encoding(folder):
#     for dirpath, dirnames, filenames in os.walk(folder):
#         for filename in filenames:
#             file_path = os.path.join(dirpath, filename)
#             with open(file_path, 'rb') as f:
#                 result = chardet.detect(f.read())
#                 original_encoding = result['encoding']
#             with open(file_path, 'r', encoding=original_encoding) as f:
#                 content = f.read()
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 f.write(content)

# def convert_encoding(folder):
#     for dirpath, dirnames, filenames in os.walk(folder):
#         for filename in filenames:
#             file_path = os.path.join(dirpath, filename)
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     content = f.read()
#             except:
#                 try:
#                     with open(file_path, 'r', encoding='gbk2312') as f:
#                         content = f.read()
#                 except:
#                     with open(file_path, 'r', encoding='gbk') as f:
#                         content = f.read()
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 f.write(content)
def convert_encoding(folder):
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if not (filename.endswith('.html') or filename.endswith('.htm')):
                continue
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                        content = f.read()
                except:
                    with open(file_path, 'r', encoding='gb18030', errors='ignore') as f:
                        content = f.read()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)


convert_encoding(r"")