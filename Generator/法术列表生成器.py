import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
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
    "玩家手册" : "PHB",
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

html_template = "../空白页模板/法术列表模板.htm"

class Spell:
    def __init__(self, content, chm_path="", source_tag="PHB"):
        self.spell_name = ""
        self.spell_name_en = ""
        self.spell_id = ""
        self.spell_subline = ""
        self.spell_content = ""
        
        self.spell_classes = []
        self.spell_level = ""
        self.spell_ritual = False
        self.spell_school = ""
        self.spell_source_tag = source_tag
        self.chm_path = chm_path
        
        content = content.replace("\r\n","").replace("\n","").replace("</H4>","</H4>\n").replace("<BR>","\n").replace("<BLOCKQUOTE","\n\n<BLOCKQUOTE").replace("<LI>","\n<LI> · ").replace("<P>","\n<P>")
        # 寻找id
        left = content.find("id=\"")+4
        right = content.find("\">",left)
        self.spell_id = content[left:right]
        lines = BeautifulSoup(content, 'html.parser').get_text().splitlines()
        print(lines[0])
        self.spell_name, self.spell_name_en = lines[0].split("｜")
        self.spell_name = self.spell_name.strip()
        self.spell_name_en = self.spell_name_en.strip()
        self.spell_subline = lines[1].strip()
        self.spell_content = "\n".join(lines[2:]).strip()
        if "仪式" in self.spell_subline:
            self.spell_ritual = True
        if "戏法" in self.spell_subline:
            self.spell_level = "戏法(0环)"
        elif "一环" in self.spell_subline:
            self.spell_level = "1环"
        elif "二环" in self.spell_subline:
            self.spell_level = "2环"
        elif "三环" in self.spell_subline:
            self.spell_level = "3环"
        elif "四环" in self.spell_subline:
            self.spell_level = "4环"
        elif "五环" in self.spell_subline:
            self.spell_level = "5环"
        elif "六环" in self.spell_subline:
            self.spell_level = "6环"
        elif "七环" in self.spell_subline:
            self.spell_level = "7环"
        elif "八环" in self.spell_subline:
            self.spell_level = "8环"
        elif "九环" in self.spell_subline:
            self.spell_level = "9环"
        else:
            print(id_and_link + " 解析出错！")
        
        for school in ["防护","咒法","预言","惑控","塑能","幻术","死灵","变化"]:
            if school in self.spell_subline:
                self.spell_school = school
                break
        for _class in class_list:
            if _class in self.spell_subline:
                self.spell_classes.append(_class)
                
    def output_id_and_link(self,_class="术士") -> str:
        if _class == "法师":
            id_and_link = "<a href=\""+self.chm_path+"#"+self.spell_id+"\">"+self.spell_school+" - "+self.spell_name+self.spell_name_en+"</a>"
        else:
            id_and_link = "<a href=\""+self.chm_path+"#"+self.spell_id+"\">"+self.spell_name+self.spell_name_en+"</a>"
        if self.spell_ritual and _class in ["法师","吟游诗人","牧师","德鲁伊","奇械师"]:
            id_and_link += "（仪式）"
        if self.spell_source_tag != "PHB":
            id_and_link += "<sup>"+self.spell_source_tag+"</sup>"
        return id_and_link
    
    def output_database(self) -> list[str]:
        output = [self.spell_name,self.spell_name_en,self.spell_source_tag,"法术",self.spell_subline,self.spell_content]
        return output

class_spell_list: dict[str, dict[str, list[Spell]]] = {}
big_spell_list: dict[str, Spell] = {}
big_spell_list_keys: list[str] = []

def process_file(file_path: str,file_name: str):
    data = ""
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gb2312") as _f:
        data = _f.read()
    data = data[data.find("<body>")+6:data.find("</body>")]
    contents = [("<H4" + content).strip() for content in data.split("<H4") if content.strip() != ""]
    id_and_link = ""
    source = ""
    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]
    for book in source_tag.keys():
        if book in chm_path:
            source = source_tag[book]
            break
    for content in contents:
        try:
            spell = Spell(content,chm_path,source)
            
            for _class in spell.spell_classes:
                if _class not in class_spell_list.keys():
                    class_spell_list[_class] = {}
                if spell.spell_level not in class_spell_list[_class].keys():
                    class_spell_list[_class][spell.spell_level] = []
                class_spell_list[_class][spell.spell_level].append(spell)
            big_spell_list[spell.spell_id] = spell
            big_spell_list_keys.append(spell.spell_id)
        except:
            print("解析出错")

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

    # 生成速查
    template = ""
    with open(html_template,mode="r",encoding="gb2312") as _f:
        template = _f.read()
    for c in class_list:
        contents = []
        for level in level_list:
            if len(class_spell_list[c][level]) != 0:
                contents.append("<h2>"+level+"</h2>\n<p>"+"<br>\n".join([spell.output_id_and_link(c) for spell in class_spell_list[c][level]])+"</p>")
        with open("./Generated/"+c+"法术速查.html",mode="w",encoding="gb2312") as _f:
            _f.write(template.replace("法术列表模板",c+"法术列表").replace("{{内容}}","\n".join(contents)))
    # 生成速查大表
    big_spell_list_keys.sort()
    print("已发现合计 "+str(len(big_spell_list_keys))+" 个法术。")
    with open("./Generated/5E万法大全.html",mode="w",encoding="gb2312") as _f:
        _f.write(template.replace("法术列表模板","5E万法大全").replace("{{内容}}","<br>\n".join([big_spell_list[spell_id].output_id_and_link() for spell_id in big_spell_list_keys])))

    template = ""
    with open("../空白页模板/法术快速复制页模板.htm",mode="r",encoding="gb2312") as _f:
        template = _f.read()
    # Workbook
    wb = Workbook()
    ws = wb.create_sheet(title="万法大全")
    for spell_id in big_spell_list_keys:
        ws.append(big_spell_list[spell_id].output_database())
    wb.save("./Generated/5E万法大全.xlsx")
    """
    with open("./Generated/法术快速复制页.html",mode="w",encoding="gb2312") as _f:
        _f.write(template.replace("法术列表模板","法术快速复制页").replace("{{内容}}","\n".join([spell.output_id_and_link for spell in big_spell_list])))
    """