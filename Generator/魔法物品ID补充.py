import os
import re
from tkinter import Tk, filedialog

# ===== 开关 =====
EXPORT_CHINESE_NAMES = False  # 是否导出中文名列表

# ⭐新增：选择模式
INPUT_MODE = "files"  # folder = 文件夹 / files = 多文件

# ===== H6黑名单（标准化后匹配）=====
BLACKLIST_TITLES = {
    "动作Action",
    "附赠动作BonusAction",
    "反应Reaction",
    "特质Trait",
    "传奇动作LegendaryAction",
}

# ===== 统计 =====
total_h6 = 0
added_id = 0
fixed_id = 0
kept_id = 0
failed = 0

chinese_names = set()


# ===== 提取英文名 =====
def extract_english_name(full_name: str):
    full_name = re.sub(r'（.*?）|\(.*?\)', '', full_name)
    full_name = re.sub(r'\+\d+', '', full_name)
    full_name = re.sub(r'[，、,]', ' ', full_name)
    full_name = full_name.strip()

    match = re.search(r'([A-Za-z][A-Za-z\s\'\-]*)$', full_name)

    if match:
        english = match.group(1).strip()
        english = "_".join(english.split())
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

        # ===== 标题标准化（方案C）=====
        normalized_inner = re.sub(r"\s+", "", inner)

        # 复数归一化
        normalized_inner = re.sub(r"Actions$", "Action", normalized_inner)
        normalized_inner = re.sub(r"Reactions$", "Reaction", normalized_inner)
        normalized_inner = re.sub(r"Traits$", "Trait", normalized_inner)

        # ===== 黑名单判断 =====
        if normalized_inner in BLACKLIST_TITLES:
            print(f"[{os.path.basename(file_path)}] ⏭ 跳过黑名单: {inner}")

            if re.search(r'id="([^"]+)"', tag_attr):
                print(f"[{os.path.basename(file_path)}] 🗑 删除黑名单ID: {inner}")
                new_attr = re.sub(r'\s*id="[^"]+"', '', tag_attr)
                return f"<H6{new_attr}>\n{inner}\n</H6>"

            return match.group(0)

        cn_name = extract_chinese_name(inner)
        if cn_name:
            chinese_names.add(cn_name)

        english_name = extract_english_name(inner)


        if not english_name:
            failed += 1
            print(f"[{os.path.basename(file_path)}] ✘ 未识别: {inner}")
            return match.group(0)

        id_match = re.search(r'id="([^"]+)"', tag_attr)

        if id_match:
            old_id = id_match.group(1)

            if old_id == english_name:
                kept_id += 1
                return match.group(0)
            else:
                fixed_id += 1
                print(f"[{os.path.basename(file_path)}] 🔧 修复ID: {old_id} → {english_name}")
                return f'<H6 id="{english_name}">\n{inner}\n</H6>'

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


# ===== 多文件处理 =====
def process_files(file_list):
    for f in file_list:
        process_file(f)


# ===== 主函数 =====
def main():
    root = Tk()
    root.withdraw()

    path = None

    # ⭐ 根据模式选择输入
    if INPUT_MODE == "folder":
        path = filedialog.askdirectory(title="选择文件夹")

    elif INPUT_MODE == "files":
        path = filedialog.askopenfilenames(
            title="选择HTML文件",
            filetypes=[("HTML files", "*.html *.htm")]
        )

    if not path:
        print("已取消")
        return

    print(f"开始处理模式：{INPUT_MODE}")

    # ===== 分发 =====
    if INPUT_MODE == "folder":
        print(f"文件夹：{path}\n")
        process_folder(path)

    else:
        print(f"文件数量：{len(path)}\n")
        process_files(path)

    print("\n====== 统计 ======")
    print(f"H6 总数：{total_h6}")
    print(f"新增ID：{added_id}")
    print(f"修复ID：{fixed_id}")
    print(f"保留ID：{kept_id}")
    print(f"未识别：{failed}")
    print(f"中文名（去重）：{len(chinese_names)}")

    # ===== 导出中文名 =====
    if EXPORT_CHINESE_NAMES:
        output_file = os.path.join(
            path if isinstance(path, str) else os.path.dirname(path[0]),
            "中文名列表.txt"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            for name in sorted(chinese_names):
                f.write(name + "\n")

        print(f"已导出中文名列表 → {output_file}")

    root.quit()


if __name__ == "__main__":
    main()