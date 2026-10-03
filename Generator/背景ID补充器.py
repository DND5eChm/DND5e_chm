import os
import re
from tkinter import Tk, filedialog


# ============================================================
# 配置
# ============================================================

# folder = 处理整个文件夹
# files  = 手动选择多个文件
INPUT_MODE = "folder"


# ============================================================
# 统计
# ============================================================

total_h3 = 0
added_id = 0
fixed_id = 0
kept_id = 0
skipped_id = 0
failed = 0


# ============================================================
# 修改模式
# None = 每次询问
# "all" = 后续全部修改
# "skip" = 后续全部跳过
# ============================================================

FIX_ID_MODE = None


# ============================================================
# 提取英文名
# ============================================================

def extract_english_name(full_name: str):

    # 去掉换行、回车
    full_name = full_name.replace("\r", "")
    full_name = full_name.replace("\n", "")

    # 去掉首尾空白
    full_name = full_name.strip()

    # 从第一个英文字符开始寻找
    match = re.search(r"[A-Za-z]", full_name)

    if not match:
        return None

    english = full_name[match.start():].strip()

    # 英文部分必须只包含：
    # 英文字母
    # 数字
    # 空格
    # 连字符
    # 撇号
    #
    # 这样可以避免把后面的中文内容错误地放进 ID。

    if not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9 \-']*",
        english
    ):
        return None

    # 空格 -> 下划线
    english = re.sub(r"\s+", "_", english)

    # 连字符 -> 下划线
    english = english.replace("-", "_")

    # 撇号删除
    english = english.replace("'", "")

    # 连续下划线合并
    english = re.sub(r"_+", "_", english)

    # 去掉首尾下划线
    english = english.strip("_")

    if not english:
        return None

    return english


# ============================================================
# 处理单个文件
# ============================================================

def process_file(file_path: str):

    global total_h3
    global added_id
    global fixed_id
    global kept_id
    global skipped_id
    global failed
    global FIX_ID_MODE

    file_name = os.path.basename(file_path)

    with open(file_path, mode="r", encoding="gbk") as f:
        content = f.read()

    # 匹配：
    #
    # <H3>侍僧 Acolyte</H3>
    #
    # <H3 >侍僧 Acolyte</H3>
    #
    # <H3 id="xxx">
    # 侍僧 Acolyte
    # </H3>
    #
    pattern = re.compile(
        r"<H3([^>]*)>(.*?)</H3>",
        re.IGNORECASE | re.DOTALL
    )

    def replace_func(match):

        global total_h3
        global added_id
        global fixed_id
        global kept_id
        global skipped_id
        global failed
        global FIX_ID_MODE

        total_h3 += 1

        tag_attr = match.group(1)
        inner = match.group(2)

        # ====================================================
        # 提取标题文字
        # ====================================================

        full_name = inner.strip()

        full_name = full_name.replace("\r", "")
        full_name = full_name.replace("\n", "")

        # 如果标题中出现 HTML 标签，暂不自动处理
        if "<" in full_name or ">" in full_name:

            failed += 1

            print(
                f"[{file_name}] ✘ 标题包含HTML标签: "
                f"{full_name}"
            )

            return match.group(0)

        # ====================================================
        # 提取英文 ID
        # ====================================================

        english_name = extract_english_name(full_name)

        if not english_name:

            failed += 1

            print(
                f"[{file_name}] ✘ 无法识别英文名: "
                f"{full_name}"
            )

            return match.group(0)

        # ====================================================
        # 检查已有 ID
        # ====================================================

        id_match = re.search(
            r'\bid\s*=\s*"([^"]+)"',
            tag_attr,
            re.IGNORECASE
        )

        # ====================================================
        # 没有 ID -> 自动添加
        # ====================================================

        if not id_match:

            added_id += 1

            print(
                f"[{file_name}] ✔ 新增ID: "
                f"{english_name}"
            )

            return (
                f'<H3 id="{english_name}">'
                f'{full_name}'
                f'</H3>'
            )

        # ====================================================
        # 已经存在 ID
        # ====================================================

        old_id = id_match.group(1)

        # ID 已经正确
        if old_id == english_name:

            kept_id += 1

            return match.group(0)

        # ====================================================
        # ID 不正确，需要询问
        # ====================================================

        print()
        print("=" * 60)
        print(f"文件：{file_name}")
        print(f"背景：{full_name}")
        print(f"当前 ID：{old_id}")
        print(f"建议 ID：{english_name}")
        print("=" * 60)

        # 后续全部修改
        if FIX_ID_MODE == "all":

            answer = "y"

        # 后续全部跳过
        elif FIX_ID_MODE == "skip":

            answer = "n"

        # 正常询问
        else:

            while True:

                answer = input(
                    "是否修改 ID？"
                    " [Y=修改 / N=跳过 / A=全部修改 / S=全部跳过]："
                ).strip().lower()

                if answer in ("y", "n", "a", "s"):
                    break

                print("请输入 Y、N、A 或 S。")

            # 设置后续处理模式
            if answer == "a":

                FIX_ID_MODE = "all"
                answer = "y"

            elif answer == "s":

                FIX_ID_MODE = "skip"
                answer = "n"

        # ====================================================
        # 修改
        # ====================================================

        if answer == "y":

            fixed_id += 1

            print(
                f"[{file_name}] 🔧 修复ID："
                f"{old_id} → {english_name}"
            )

            # 删除原 ID
            new_attr = re.sub(
                r'\s*\bid\s*=\s*"[^"]*"',
                "",
                tag_attr,
                flags=re.IGNORECASE
            )

            # 重新生成 H3
            return (
                f'<H3 id="{english_name}"{new_attr}>'
                f'{full_name}'
                f'</H3>'
            )

        # ====================================================
        # 跳过
        # ====================================================

        else:

            skipped_id += 1

            print(
                f"[{file_name}] ⏭ 跳过："
                f"{old_id}"
            )

            return match.group(0)

    # ========================================================
    # 执行替换
    # ========================================================

    new_content = pattern.sub(
        replace_func,
        content
    )

    # ========================================================
    # 只有真正发生修改才写文件
    # ========================================================

    if new_content != content:

        with open(file_path, mode="w", encoding="gbk") as f:
            f.write(new_content)


# ============================================================
# 文件夹模式
# ============================================================

def process_folder(folder_path: str):

    for root, dirs, files in os.walk(folder_path):

        for file in files:

            if (
                file.lower().endswith(".html")
                or file.lower().endswith(".htm")
            ):

                file_path = os.path.join(
                    root,
                    file
                )

                print()
                print(
                    "开始处理："
                    + file_path
                )

                process_file(file_path)


# ============================================================
# 多文件模式
# ============================================================

def process_files(file_list):

    for file_path in file_list:

        print()
        print(
            "开始处理："
            + file_path
        )

        process_file(file_path)


# ============================================================
# 主函数
# ============================================================

def main():

    root = Tk()
    root.withdraw()

    path = None

    # ========================================================
    # 选择输入模式
    # ========================================================

    if INPUT_MODE == "folder":

        path = filedialog.askdirectory(
            title="选择背景文件夹"
        )

    elif INPUT_MODE == "files":

        path = filedialog.askopenfilenames(
            title="选择背景HTML文件",
            filetypes=[
                (
                    "HTML files",
                    "*.html *.htm"
                )
            ]
        )

    else:

        print(
            f"错误：INPUT_MODE = {INPUT_MODE}"
            "，只能使用 folder 或 files。"
        )

        root.quit()
        return

    # ========================================================
    # 取消
    # ========================================================

    if not path:

        print("已取消。")
        root.quit()
        return

    # ========================================================
    # 开始处理
    # ========================================================

    print()
    print("====== 背景 ID 批量处理 ======")
    print(
        f"处理模式：{INPUT_MODE}"
    )

    if INPUT_MODE == "folder":

        print(
            f"文件夹：{path}"
        )

        process_folder(path)

    else:

        print(
            f"文件数量：{len(path)}"
        )

        process_files(path)

    # ========================================================
    # 统计
    # ========================================================

    print()
    print("====== 统计 ======")

    print(
        f"H3 总数：{total_h3}"
    )

    print(
        f"新增 ID：{added_id}"
    )

    print(
        f"修复 ID：{fixed_id}"
    )

    print(
        f"正确 ID：{kept_id}"
    )

    print(
        f"无需修改：{skipped_id}"
    )

    print(
        f"未识别：{failed}"
    )

    root.quit()


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":

    main()
