import os
from tkinter import Tk, filedialog
from 文件遍历 import get_path_relative, walk_through_files


def process_file(file_path: str,file_name: str):
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gbk") as _f:
        contents = _f.readlines()
    edited = False
    for content in contents:
        if "<H4>" in content:
            left = content.find("<H4>")
            right = content.find("</H4>")
            full_name = content[left+4:right].strip()
            if "丨" in content: #神经小符号防呆，正确符号应该是那个｜
                full_name = full_name.replace("丨","｜")
                content = content.replace("丨","｜")
                edited = True
            if "｜" in full_name:
                english_name = full_name.split("｜")[1].replace(" ","_")
                content = content.replace("<H4>","<H4 id=\""+english_name+"\">",1)
                edited = True
                print(full_name + "补充ID：" + english_name)
            else:
                print(full_name + "格式有误，无法解析")
        new_contents.append(content)
    
    if edited:
        with open(file_path,mode="w",encoding="gbk") as _f:
            _f.writelines(new_contents)
        print("已完成补充")
    else:
        print("已检查，并不需要补充ID（或者格式不太正确？）")

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