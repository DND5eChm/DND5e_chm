import os
import re
from tkinter import Tk, filedialog


# ===== 开关 =====
EXPORT_CHINESE_NAMES = False  # 是否导出中文名列表


# ===== 统计 =====
total_h6 = 0
added_id = 0
fixed_id = 0
kept_id = 0
failed = 0

chinese_names = set()


# ===== 提取英文名 =====
def extract_english_name(full_name: str):
    # 去括号（中英文）
    full_name = re.sub(r'（.*?）|\(.*?\)', '', full_name)

    # 去 +1 +2 +3
    full_name = re.sub(r'\+\d+', '', full_name)

    # 替换中文标点为空格
    full_name = re.sub(r'[，、,]', ' ', full_name)

    full_name = full_name.strip()

    # 匹配结尾英文
    match = re.search(r'([A-Za-z][A-Za-z\s\'\-]*)$', full_name)

    if match:
        english = match.group(1).strip()

        # 空格 → _
        english = "_".join(english.split())

        # 保留 '（关键）
        english = re.sub(r"[^A-Za-z0-9_']", "", english)

        return english

    return None


# ===== 提取中文名 =====
def extract_chinese_name(full_name: str):
    match = re.match(r'^([\u4e00-\u9fa5·]+)', full_name)
    if match:
        return match.group(1).strip()
    return None


# ===== 处理文件 =====
def process_file(file_path: str):
    global total_h6, added_id, fixed_id, kept_id, failed

    with open(file_path, mode="r", encoding="gbk") as f:
        content = f.read()

    pattern = re.compile(r"<H6(.*?)>(.*?)</H6>", re.DOTALL)

    def replace_func(match):
        global total_h6, added_id, fixed_id, kept_id, failed

        total_h6 += 1

        tag_attr = match.group(1)
        inner = match.group(2).strip()

        # ===== 收集中文名 =====
        cn_name = extract_chinese_name(inner)
        if cn_name:
            chinese_names.add(cn_name)

        # ===== 提取正确英文名 =====
        english_name = extract_english_name(inner)

        if not english_name:
            failed += 1
            print(f"[{os.path.basename(file_path)}] ✘ 未识别: {inner}")
            return match.group(0)

        # ===== 查找已有 id =====
        id_match = re.search(r'id="([^"]+)"', tag_attr)

        if id_match:
            old_id = id_match.group(1)

            # ✅ 核心：必须完全一致才保留
            if old_id == english_name:
                kept_id += 1
                return match.group(0)
            else:
                fixed_id += 1
                print(f"[{os.path.basename(file_path)}] 🔧 修复ID: {old_id} → {english_name}")
                return f'<H6 id="{english_name}">\n{inner}\n</H6>'

        # ===== 没有 id =====
        added_id += 1
        print(f"[{os.path.basename(file_path)}] ✔ 新增ID: {english_name}")

        return f'<H6 id="{english_name}">\n{inner}\n</H6>'

    new_content = pattern.sub(replace_func, content)

    if new_content != content:
        with open(file_path, mode="w", encoding="gbk") as f:
            f.write(new_content)


# ===== 批量处理 =====
def process_folder(folder_path: str):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".html") or file.endswith(".htm"):
                process_file(os.path.join(root, file))


# ===== 主函数 =====
def main():
    root = Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(title="选择要处理的文件夹")

    if not folder_path:
        print("已取消")
        return

    print(f"开始处理：{folder_path}\n")

    process_folder(folder_path)

    print("\n====== 统计 ======")
    print(f"H6 总数：{total_h6}")
    print(f"新增ID：{added_id}")
    print(f"修复ID：{fixed_id}")
    print(f"保留ID：{kept_id}")
    print(f"未识别：{failed}")
    print(f"中文名（去重）：{len(chinese_names)}")

    # ===== 导出中文名 =====
    if EXPORT_CHINESE_NAMES:
        output_file = os.path.join(folder_path, "中文名列表.txt")

        with open(output_file, "w", encoding="utf-8") as f:
            for name in sorted(chinese_names):
                f.write(name + "\n")

        print(f"已导出中文名列表 → {output_file}")

    root.quit()


if __name__ == "__main__":
    main()