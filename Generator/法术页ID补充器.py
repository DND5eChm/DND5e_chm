import os
from tkinter import Tk, filedialog
from 文件遍历 import get_path_relative, walk_through_files


def process_file(file_path: str, file_name: str):
    contents = []
    new_contents = []

    with open(file_path, mode="r", encoding="gbk") as _f:
        contents = _f.readlines()

    edited = False
    changed_list = []
    error_list = []

    i = 0

    while i < len(contents):
        content = contents[i]

        # 找 <H4>、<H4 >、<H4    > 等形式
        if "<H4" in content and ">" in content:

            # 找 </H4>
            end_line = i

            while end_line < len(contents):
                if "</H4>" in contents[end_line]:
                    break
                end_line += 1

            if end_line >= len(contents):
                error_list.append("H4格式有误，找不到</H4>")
                new_contents.append(content)
                i += 1
                continue

            # 把整个 H4 合并起来
            h4_content = "".join(contents[i:end_line + 1])

            # 找 <H4 ...>
            left = h4_content.find("<H4")
            h4_start_end = h4_content.find(">", left)

            # 找 </H4>
            right = h4_content.find("</H4>", h4_start_end)

            if h4_start_end == -1 or right == -1:
                error_list.append("H4格式有误，无法解析")
                new_contents.extend(contents[i:end_line + 1])
                i = end_line + 1
                continue

            # 提取 H4 中的文字
            full_name = h4_content[h4_start_end + 1:right]

            # 去掉换行、回车和首尾空白
            full_name = full_name.replace("\r", "")
            full_name = full_name.replace("\n", "")
            full_name = full_name.strip()

            # 修正错误的竖线符号
            if "丨" in full_name:
                full_name = full_name.replace("丨", "｜")

            # 没有 ｜，无法提取英文名
            if "｜" not in full_name:
                error_list.append(full_name + "：格式有误，无法解析")
                new_contents.extend(contents[i:end_line + 1])
                i = end_line + 1
                continue

            # 提取英文名
            english_name = full_name.split("｜", 1)[1].strip()
            english_name = english_name.replace(" ", "_")

            # 生成标准格式
            new_h4 = (
                '<H4 id="' + english_name + '">'
                + full_name +
                '</H4>\n'
            )

            # 原始 H4
            old_h4 = "".join(contents[i:end_line + 1])

            # 只有真的不同才修改
            if old_h4 != new_h4:
                edited = True
                changed_list.append(
                    full_name + " → " + english_name
                )
                new_contents.append(new_h4)
            else:
                # 完全正确，不输出
                new_contents.append(old_h4)

            # 跳过已经处理的 H4
            i = end_line + 1

        else:
            new_contents.append(content)
            i += 1

    # 写入文件
    if edited:
        with open(file_path, mode="w", encoding="gbk") as _f:
            _f.writelines(new_contents)

    # ===== 最后统一输出结果 =====

    if changed_list:
        print("\n【已修改】")
        for item in changed_list:
            print("  " + item)

    if error_list:
        print("\n【有问题】")
        for item in error_list:
            print("  " + item)

    if not changed_list and not error_list:
        print("  无需修改")

if __name__ == "__main__":
    #TARGET = input("输入要处理的文件的名字：")
    #walk_through_files(process_file,TARGET)
    root = Tk()
    root.withdraw()
    filetype = [("页面",".htm .html")]
    spell_paths = filedialog.askopenfiles(title="请选择要打开的文件",initialdir="../", filetypes=filetype)
    if spell_paths == None:
        print("已取消。")
    else:
        print("已获取文件列表")
        spell_path_list = list(spell_paths)
        for spell_path in spell_path_list:
            relative_path = get_path_relative(spell_path.name)
            print("开始为"+relative_path+"补充法术ID。")
            walk_through_files(process_file,relative_path)
    root.quit()