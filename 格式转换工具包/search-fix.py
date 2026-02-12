import os


def process_file(file_path, replace_rules):
    """
    读取文件，依次执行所有替换规则，如果有变化则保存。
    
    file_path: 文件绝对路径
    replace_rules: 包含元组的列表 [ (旧字符串, 新字符串), ... ]
    """
    if not os.path.exists(file_path):
        print(f"[跳过] 文件不存在: {file_path}")
        return

    try:
        # 读取文件 (UTF-8)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        total_replaced_count = 0

        # 依次执行替换规则
        for old_str, new_str in replace_rules:
            count = content.count(old_str)
            if count > 0:
                content = content.replace(old_str, new_str)
                total_replaced_count += count

        # 如果内容有变化，则写入
        if total_replaced_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(
                f"[成功] {os.path.basename(file_path)}: 执行了 {total_replaced_count} 处替换")
        else:
            print(f"[未变] {os.path.basename(file_path)}")

    except Exception as e:
        print(f"[错误] 处理文件 {os.path.basename(file_path)} 时出错: {e}")


def main():
    # 基础目录配置
    base_dir = r"F:\TRPG-CHM\DND5e_chm_output\Web Help\topics\速查"

    print("--- 开始执行批量替换脚本 (UTF-8) ---")
    print(f"根目录: {base_dir}\n")

    # =======================================================
    # 任务 1: 处理 "5E万兽大全.html"
    # =======================================================
    target_file = os.path.join(base_dir, "5E万兽大全.html")
    print(">>> 正在处理: 5E万兽大全.html")

    # 规则列表
    rules_monster = [
        ('<a href="', '<A href="../')
    ]
    process_file(target_file, rules_monster)

    print("-" * 40)

    # =======================================================
    # 任务 2: 处理 "法术速查" 文件夹下的所有 html
    # =======================================================
    sub_folder = os.path.join(base_dir, "法术速查")
    print(f">>> 正在处理文件夹: 法术速查")

    if os.path.exists(sub_folder):
        # 定义该文件夹内的规则列表
        # 注意：这里定义了两个规则，脚本会依次执行
        rules_spells = [
            # 规则 A: 普通链接
            ('<a href="', '<A href="../../'),
            # 规则 B: legacy 类链接
            ('<a class="legacy" href="', '<a class="legacy" href="../../')
        ]

        files_found = 0
        for filename in os.listdir(sub_folder):
            if filename.lower().endswith(".html") or filename.lower().endswith(".htm"):
                full_path = os.path.join(sub_folder, filename)
                process_file(full_path, rules_spells)
                files_found += 1

        if files_found == 0:
            print("该文件夹内未找到 HTML 文件。")
    else:
        print(f"[警告] 文件夹不存在: {sub_folder}")

    print("\n--- 全部处理完成 ---")
    input("按回车键退出...")


if __name__ == "__main__":
    main()
