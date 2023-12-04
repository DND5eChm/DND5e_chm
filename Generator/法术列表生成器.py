import os
from 文件遍历 import walk_through_files

spell_file_list = [
    "玩家手册/魔法/法术详述",
    "珊娜萨的万事指南/法术/法术详述",
    "塔莎的万事坩埚/法术/法术详述",
    "拉尼卡公会长指南/思想编码.htm",
    "荒洲探险家指南/玩家选项/秘迹使法术详述.htm",
    "艾奎兹玄有限责任公司/玩家选项/新法术详述.htm",
    "费资本的巨龙宝库/玩家选项/巨龙法术详述.htm",
    "斯翠海文：混沌研习/玩家选项/法术详述.html",
    "印记城与外域/新法术详述.htm",
    "万象无常书/贤者/卡牌法术详述.htm"
]
source_tag: dict[str,str] = {
    "珊娜萨的万事指南" : "XGE",
    "塔莎的万事坩埚" : "TCE",
    "拉尼卡公会长指南" : "GGR",
    "荒洲探险家指南" : "EGW",
    "艾奎兹玄有限责任公司" : "AI",
    "费资本的巨龙宝库" : "FTD",
    "斯翠海文" : "SCC",
    "印记城与外域" : "SO",
    "万象无常书" : "BMT"
}
class_list = [
    "吟游诗人",
    "牧师",
    "德鲁伊",
    "圣武士",
    "游侠",
    "术士",
    "法师",
    "邪术师",
    "奇械师"
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
html_template = "../空白页模板/法术列表模板.htm"

def process_file(file_path: str,file_name: str):
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gb2312") as _f:
        contents = _f.readlines()
    level = file_name.replace(".html","").replace(".htm","")
    id_and_link = ""
    total_sup = ""
    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]
    for book in source_tag.keys():
        if book in chm_path:
            total_sup = source_tag[book]
            break
    print(chm_path)
    for content in contents:
        if "<H4 id=" in content:
            left = content.find("<H4 id=\"")
            right = content.find("\">")
            id = content[left+8:right]
            left = right+2
            right = content.find("</H4>")
            full_name = content[left:right].replace("｜","")
            id_and_link = "<a href=\""+chm_path+"#"+id+"\">"+full_name+"</a>"
            big_spell_list.append(id_and_link+"<br>")
        elif "<EM>" in content and id_and_link != "":
            level = "未知"
            left = content.find("<EM>")
            right = content.find("</EM>")
            if right == -1:
                print(id_and_link)
            tce_line = ""
            sub_line = content[left+3:right]
            if "仪式" in sub_line:
                id_and_link = id_and_link + "（仪式）"
            if "TCE" in sub_line:
                tce_line = sub_line.split("TCE：")[1]

            if "戏法" in sub_line:
                level = "戏法(0环)"
            elif "一环" in sub_line:
                level = "1环"
            elif "二环" in sub_line:
                level = "2环"
            elif "三环" in sub_line:
                level = "3环"
            elif "四环" in sub_line:
                level = "4环"
            elif "五环" in sub_line:
                level = "5环"
            elif "六环" in sub_line:
                level = "6环"
            elif "七环" in sub_line:
                level = "7环"
            elif "八环" in sub_line:
                level = "8环"
            elif "九环" in sub_line:
                level = "9环"
            else:
                print(id_and_link + " 解析出错！")
            
            for c in class_list:
                if c in sub_line:
                    sup = total_sup
                    output = id_and_link
                    if c in tce_line:
                        sup += "TCE扩表"
                    if c == "法师":
                        for school in ["防护","咒法","预言","附魔","塑能","幻术","死灵","变化"]:
                            if school in sub_line:
                                output = output.replace("\">","\">" + school + " - ")
                            
                    if sup != "":
                        class_spell_list[c][level].append(output+"<sup>"+sup+"</sup>")
                    else:
                        class_spell_list[c][level].append(output)
            id_and_link = ""

if __name__ == "__main__":

    target_folder = os.path.exists("./Generated")
    if not target_folder:
        os.makedirs("./Generated")

    for c in class_list:
        class_spell_list[c] = {}
        for level in level_list:
            class_spell_list[c][level]: list[str] = []
    for file in spell_file_list:
        walk_through_files(process_file,file)

    template = ""
    with open(html_template,mode="r",encoding="gb2312") as _f:
        template = _f.read()
    for c in class_list:
        contents = []
        for level in level_list:
            if len(class_spell_list[c][level]) != 0:
                contents.append("<h2>"+level+"</h2>\n<p>"+"<br>\n".join(class_spell_list[c][level])+"</p>")
        with open("./Generated/"+c+"法术速查.html",mode="w",encoding="gb2312") as _f:
            _f.write(template.replace("法术列表模板",c+"法术列表").replace("{{内容}}","\n".join(contents)))
    big_spell_list.sort()
    with open("./Generated/5E万法大全.html",mode="w",encoding="gb2312") as _f:
        _f.write(template.replace("法术列表模板","5E万法大全").replace("{{内容}}","\n".join(big_spell_list)))

    template = ""
    with open("../空白页模板/法术快速复制页模板.htm",mode="r",encoding="gb2312") as _f:
        template = _f.read()
    with open("./Generated/法术快速复制页.html",mode="w",encoding="gb2312") as _f:
        _f.write(template.replace("法术列表模板","法术快速复制页").replace("{{内容}}","\n".join(big_spell_list)))
        