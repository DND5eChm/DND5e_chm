import os
from 文件遍历 import walk_through_files

PATH = "D:/GitHub/DND5e_chm/玩家手册/魔法/法术详述"
LINK_PATH = "玩家手册/魔法/法术详述/"
TARGET = "珊娜萨的万事指南/法术/法术详述"
class_spell_list: dict[str, dict[str, list[str]]] = {}
big_spell_list: list[str] = []
html_template = "D:/GitHub/DND5e_chm/空白页模板/法术列表模板.htm"

def process_file(file_path: str,file_name: str):
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gb2312") as _f:
        contents = _f.readlines()
    for content in contents:
        if "<H4>" in content:
            left = content.find("<H4>")
            right = content.find("</H4>")
            full_name = content[left+4:right].strip()
            if "｜" in full_name:
                english_name = full_name.split("｜")[1].replace(" ","_")
                content = content.replace("<H4>","<H4 id=\""+english_name+"\">",1)
                print(english_name)
            else:
                print(file_path + "的" + full_name + "格式有误！")
        new_contents.append(content)
    
    with open(file_path,mode="w",encoding="gb2312") as _f:
        _f.writelines(new_contents)

if __name__ == "__main__":
    walk_through_files()
     