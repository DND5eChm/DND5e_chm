import os
import re
from tkinter import Tk, filedialog


def extract_english_name(full_name: str):
    # 去掉中文括号内容（防干扰）
    full_name = re.sub(r'（.*?）', '', full_name)

    words = full_name.strip().split()
    english_parts = []

    for word in reversed(words):
        # 只匹配纯英文单词（允许 ' 和 -）
        if re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", word):
            english_parts.append(word)
        else:
            break

    if english_parts:
        english_name = "_".join(reversed(english_parts))
        # 转小写 + 去非法字符
        english_name = english_name.lower()
        english_name = re.sub(r"[^a-z0-9_]", "", english_name)
        return english_name

    return None


def process_file(file_path: str):
    with open(file_path, mode="r", encoding="gbk") as f:
        content = f.read()

    # 用正则匹配整个 H6 块（支持换行）
    pattern = re.compile(r"<H6>(.*?)</H6>", re.DOTALL)

    edited = False

    def replace_func(match):
        nonlocal edited

        inner = match.group(1).strip()
        english_name = extract_english_name(inner)

        if english_name:
            edited = True
            print(f"{inner} → id=\"{english_name}\"")
            return f'<H6 id="{english_name}">\n{inner}\n</H6>'
        else:
            print(f"{inner} 未找到英文名")
            return match.group(0)

    new_content = pattern.sub(replace_func, content)

    if edited:
        with open(file_path, mode="w", encoding="gbk") as f:
            f.write(new_content)
        print(f"✔ 已完成：{file_path}")
    else:
        print(f"○ 无需修改：{file_path}")


def main():
    root = Tk()
    root.withdraw()

    file_paths = filedialog.askopenfilenames(
        title="选择要处理的HTML文件",
        filetypes=[("HTML files", "*.htm *.html")]
    )

    if not file_paths:
        print("已取消")
        return

    for path in file_paths:
        print(f"\n处理文件：{path}")
        process_file(path)

    print("\n全部处理完成")
    root.quit()


if __name__ == "__main__":
    main()