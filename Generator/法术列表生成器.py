import os
from 文件遍历 import walk_through_files

PATH = "D:/GitHub/DND5e_chm/玩家手册/魔法/法术详述"
LINK_PATH = "玩家手册/魔法/法术详述/"
spell_file_list = [
    "玩家手册/魔法/法术详述",
    "珊娜萨的万事指南/法术/法术详述",
    "印记城与外域/新法术.htm",
    "圣武士",
    "游侠",
    "术士",
    "法师",
    "邪术师"
]
class_list = [
    "吟游诗人",
    "牧师",
    "德鲁伊",
    "圣武士",
    "游侠",
    "术士",
    "法师",
    "邪术师"
]
level_list = [
    "戏法(0环)",
    "1环",
    "2环",
    "3环",
    "4环",
    "5环",
    "6环",
    "7环",
    "8环",
    "9环",
]
class_spell_list: dict[str, dict[str, list[str]]] = {}
big_spell_list: list[str] = []
html_template = "D:/GitHub/DND5e_chm/空白页模板/法术列表模板.htm"

def process_file(file_path: str,file_name: str):
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gb2312") as _f:
        contents = _f.readlines()
    level = file_name.replace(".html","").replace(".htm","")
    id_and_link = ""
    for content in contents:
        if "<H4 id=" in content:
            left = content.find("<H4 id=\"")
            right = content.find("\">")
            id = content[left+8:right]
            left = right+2
            right = content.find("</H4>")
            full_name = content[left:right].replace("｜","")
            id_and_link = "<a href=\""+LINK_PATH+file_name+"#"+id+"\">"+full_name+"</a>"
            big_spell_list.append(id_and_link+"<br>")
        elif "<EM>" in content:
            left = content.find("<EM>")
            right = content.find("</EM>")
            sub_line = content[left+3:right]
            tce_line = ""
            if "仪式" in sub_line:
                id_and_link = id_and_link + "（仪式）"
            if "TCE" in sub_line:
                tce_line = sub_line.split("TCE：")[1]
                sub_line = sub_line.split("TCE：")[0]
            for c in class_list:
                if c in sub_line:
                    class_spell_list[c][level].append(id_and_link+"")
                elif c in tce_line:
                    class_spell_list[c][level].append(id_and_link+"（TCE扩表）")

            
    '''
    for content in contents:
        if "<H4>" in content:
            left = content.find("<H4>")
            right = content.find("</H4>")
            full_name = content[left+4:right]
            if "｜" in full_name:
                english_name = full_name.split("｜")[1].replace(" ","_")
                content = content.replace("<H4>","<H4 id=\""+english_name+"\">",1)
                print(english_name)
            else:
                print(file_path + "的" + full_name + "格式有误！")
        new_contents.append(content)
    
    with open(file_path,mode="w",encoding="gb2312") as _f:
        _f.writelines(new_contents)
    '''

if __name__ == "__main__":
    for c in class_list:
        class_spell_list[c] = {}
        for level in level_list:
            class_spell_list[c][level]: list[str] = []
    walk_through_files()
    template = ""
    with open(html_template,mode="r",encoding="gb2312") as _f:
        template = _f.read()
    for c in class_list:
        contents = []
        for level in level_list:
            if len(class_spell_list[c][level]) != 0:
                contents.append("<h2>"+level+"</h2>\n<p>"+"<br>\n".join(class_spell_list[c][level])+"</p>")
        with open(PATH+"/"+c+"法术列表.html",mode="w",encoding="gb2312") as _f:
            _f.write(template.replace("法术列表模板",c+"法术列表").replace("{{内容}}","\n".join(contents)))
        