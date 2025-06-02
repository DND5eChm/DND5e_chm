import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
from 文件遍历 import walk_through_files


spell_file_list = [
    "玩家手册/魔法/法术详述",
    "珊娜萨的万事指南/法术/法术详述",
    "塔莎的万事坩埚/法术/法术详述",
    "拉尼卡公会长指南/思想编码.htm",
    "艾奎兹玄有限责任公司/玩家选项/新法术详述.htm",
    "费资本的巨龙宝库/玩家选项/巨龙法术详述.htm",
    "斯翠海文：混沌研习/玩家选项/法术详述.html",
    "星界冒险者指南/新法术详述.htm",
    "印记城与外域/新法术详述.htm",
    "万象无常书/贤者/卡牌法术详述.htm",
    "玩家手册2024/法术详述",
    "模组/夸力许/新法术.html"
]

source_tag: dict[str,str] = {
    "玩家手册" : "PHB14",
    "珊娜萨的万事指南" : "XGE",
    "塔莎的万事坩埚" : "TCE",
    "拉尼卡公会长指南" : "GGR",
    "艾奎兹玄有限责任公司" : "AI",
    "费资本的巨龙宝库" : "FTD",
    "斯翠海文：混沌研习" : "SCC",
    "星界冒险者指南" : "AAG",
    "印记城与外域" : "SO",
    "万象无常书" : "BMT",
    "玩家手册2024" : "PHB24",
    "模组" : "模组"
}
source_priority: dict[str,int] = {
    "PHB24": 0, # 最高优先级
    "PHB14": 1,   # 第二优先级
    "XGE": 2,
    "TCE": 3,
    "FTD": 4,
    "BMT": 5,
    "GGR": 6,
    "AI": 7,
    "EGW": 8,
    "SCC": 9,
    "AAG": 10,
    "SO": 11,
    "模组": 12
}

short_cut: dict[str,str] = {
    "圣武士" : "帕",
    "吟游诗人" : "诗",
    "牧师" : "牧",
    "德鲁伊" : "德",
    "魔契师" : "锁",
    "游侠" : "软",
    "术士" : "术",
    "法师" : "法",
    "奇械师" : "械",
    "其他" : "无"
}

class_list = ["吟游诗人","牧师","德鲁伊","圣武士","游侠","术士","法师","魔契师","奇械师"]

level_list = ["戏法(零环)","一环","二环","三环","四环","五环","六环","七环","八环","九环"]

spell_conflict: dict[str,str] = {
    "Feeblemind": "zzzzzzzzzFeeblemind",      
    "Branding_Smite": "zzzzzzzzzBranding_Smite"  
}

html_template = "../空白页模板/法术列表模板.htm"
html_template_big = "../空白页模板/法术大速查模板.htm"

class Spell:
    def __init__(self, content, chm_path="", source_tag="PHB14"):
        self.spell_name = ""
        self.spell_name_en = ""
        self.spell_id = ""
        self.spell_subline = ""
        self.spell_content = ""
        
        self.spell_classes = []
        self.spell_level = ""
        self.spell_verbal = False
        self.spell_somatic = False
        self.spell_material = False
        self.spell_material_sp = False
        self.spell_ritual = False
        self.spell_concentration = False
        self.spell_school = ""
        self.spell_source_tag = source_tag
        self.spell_source_priority = source_priority[source_tag]
        
        self.chm_path = chm_path
        self.legacy = False
        
        content = content.strip().replace("\r\n","").replace("\n","").replace("</H4>","</H4>\n").replace("<BR>","\n").replace("<BLOCKQUOTE","\n\n<BLOCKQUOTE").replace("<LI>","\n<LI> · ").replace("<P>","\n<P>")
        # 寻找id
        left = content.find("id=\"")+4
        right = content.find("\">",left)
        self.spell_id = content[left:right].strip()
        lines = BeautifulSoup(content, 'html.parser').get_text().splitlines()
        self.spell_name, self.spell_name_en = lines[0].split("｜")
        self.spell_name = self.spell_name.strip()
        self.spell_name_en = self.spell_name_en.strip()
        # 处理正文
        self.spell_subline = lines[1].strip()
        self.spell_content = "\n".join(lines[2:]).strip()
        print(self.spell_name+" · "+self.spell_subline)
        if "仪式" in self.spell_subline or "或仪式" in lines[2]:
            self.spell_ritual = True
        if "专注" in lines[5]:
            self.spell_concentration = True
        if "V" in lines[4]:
            self.spell_verbal = True
        if "S" in lines[4]:
            self.spell_somatic = True
        if "M" in lines[4]:
            self.spell_material = True
            if "价值" in lines[4] or "耗材" in lines[4] or "消耗" in lines[4]:
                self.spell_material_sp = True
        if "戏法" in self.spell_subline:
            self.spell_level = "戏法(零环)"
        elif "环" in self.spell_subline:
            for level in ["一环","二环","三环","四环","五环","六环","七环","八环","九环"]:
                if level in self.spell_subline:
                    self.spell_level = level
                    break
        else:
            print(id_and_link + " 解析出错！")
        
        for school in ["防护","咒法","预言","惑控","塑能","幻术","死灵","变化"]:
            if school in self.spell_subline:
                self.spell_school = school
                break
        for _class in class_list:
            if _class in self.spell_subline:
                self.spell_classes.append(_class)
        if "邪术师" in self.spell_subline:
            self.spell_classes.append("魔契师")
        if len(self.spell_classes) == 0:  # 如果没有匹配到任何职业
            self.spell_classes.append("其他")
                
    def output_id_and_link(self,_class="万法大全") -> str:
        display_name = self.spell_name+self.spell_name_en
        
          # 职业判断逻辑显示学派
        if _class in ["法师"]:
            display_name = self.spell_school+" - "+display_name

        # if self.spell_ritual and _class in ["法师","吟游诗人","牧师","德鲁伊","奇械师", "万法大全"]:
        
        if self.legacy:
            id_and_link = "<a class=\"legacy\" href=\""+self.chm_path+"#"+self.spell_id+"\">"+display_name+"</a>"
        else:
            id_and_link = "<a href=\""+self.chm_path+"#"+self.spell_id+"\">"+display_name+"</a>"
        
        if _class == "万法大全":
            tags = [
                self.spell_school,
                " ".join(self.spell_classes),
                self.spell_level,
                self.spell_source_tag
            ]
            if self.spell_verbal:
                tags.append("言语")
            if self.spell_somatic:
                tags.append("姿势")
            if self.spell_material:
                tags.append("材料")
            if self.spell_material_sp:
                tags.append("价耗")
            if self.spell_ritual:
                tags.append("仪式")
            if self.spell_concentration:
                tags.append("专注")
            labels = [
                id_and_link, #法术名（带链接）
                self.spell_level, #法术环阶
                self.spell_school, #法术学派
                " ".join([short_cut[_class] for _class in self.spell_classes]), #法术职业简写
                "V" if self.spell_verbal else "×", #言语成分
                "S" if self.spell_somatic else "×", #姿势成分
                "M*" if self.spell_material_sp else ("M" if self.spell_material else "×"), #材料成分
                "√" if self.spell_ritual else "×", #
                "√" if self.spell_concentration else "×", #专注
                self.spell_source_tag #来源
            ]
            id_and_link = "<TR tags=\"" +" ".join(tags)+"\" spell=\""+self.spell_name+self.spell_name_en+"\"><TD>"+"</TD><TD>".join(labels)+"</TD></TR>"
        elif self.spell_source_tag not in ["","PHB14","PHB24"]: #角标
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
    with open(file_path,mode="r",encoding="gbk") as _f:
        data = _f.read()
    data = data[data.find("<body>")+6:data.find("</body>")]
    contents = [("<H4" + content).strip() for content in data.split("<H4") if content.strip() != ""]
    id_and_link = ""
    source = ""
    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]
    '''
    for book in source_tag.keys():
        if book in chm_path:
            source = source_tag[book]
            break
    '''
    book = chm_path.split("/")[0]
    if book in source_tag.keys():
        source = source_tag[book]
    else:
        source = book
    # 获取资源
    for content in contents:
        try:
            # 获取法术
            spell = Spell(content,chm_path,source)
            
            for _class in spell.spell_classes:
                if _class not in class_spell_list.keys():
                    class_spell_list[_class] = {}
                if spell.spell_level not in class_spell_list[_class].keys():
                    class_spell_list[_class][spell.spell_level] = []
                class_spell_list[_class][spell.spell_level].append(spell)
            
            if spell.spell_id in big_spell_list.keys():
                big_spell_list[spell.spell_id].legacy = True
                big_spell_list["zzzzzzzzz"+spell.spell_id] = big_spell_list[spell.spell_id]
                big_spell_list_keys.append("zzzzzzzzz"+spell.spell_id)
            elif spell.spell_id in spell_conflict.keys():#手动冲突检测
                new_id = spell_conflict[spell.spell_id]
                big_spell_list[new_id] = spell
                big_spell_list_keys.append(new_id)
                spell.legacy = True  # 标记为过时
            else:
                big_spell_list[spell.spell_id] = spell
                big_spell_list_keys.append(spell.spell_id)
            
            big_spell_list[spell.spell_id] = spell
        except:
            if len(content) > 40:
                print(content[:40]+"... 解析出错")
            else:
                print(content+" 解析出错")

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
    template_big = ""
    
    with open(html_template,mode="r",encoding="gbk") as _f:
        template = _f.read()
    with open(html_template_big,mode="r",encoding="gbk") as _f:
        template_big = _f.read()
    for c in class_list:
        contents = []
        for level in level_list:
            if len(class_spell_list[c][level]) != 0:
                # 去legacy，排序并输出
                sorted_spells = [spell for spell in class_spell_list[c][level] if not spell.legacy or c == "奇械师"] # 忽略legacy内容
                sorted_spells = sorted(sorted_spells,key=lambda x: (x.spell_source_priority,x.spell_name_en))# 排序：来源优先，法术名次优先
                contents.append("<h2>"+level+"</h2>\n<p>"+"<br>\n".join([spell.output_id_and_link(c) for spell in sorted_spells])+"</p>")
        with open("../速查/法术速查/"+c+"法术速查.html",mode="w",encoding="gbk") as _f:
            _f.write(template.replace("法术列表模板",c+"法术列表").replace("{{内容}}","\n".join(contents)))

    # 生成速查大表
    big_spell_list_keys.sort()
    print("已发现合计 "+str(len(big_spell_list_keys))+" 个法术。")
    with open("../速查/法术速查/5E万法大全.html",mode="w",encoding="gbk") as _f:
        _f.write(template_big.replace("法术列表模板","5E万法大全").replace("{{内容}}","\n".join([big_spell_list[spell_id].output_id_and_link(_class="万法大全") for spell_id in big_spell_list_keys])))
    

    """
    template = ""
    with open("../空白页模板/法术快速复制页模板.htm",mode="r",encoding="gbk") as _f:
        template = _f.read()
    # Workbook
    wb = Workbook()
    ws = wb.create_sheet(title="万法大全")
    for spell_id in big_spell_list_keys:
        ws.append(big_spell_list[spell_id].output_database())
    wb.save("../速查/法术速查/5E万法大全.xlsx")
    
    with open("./Generated/法术快速复制页.html",mode="w",encoding="gbk") as _f:
        _f.write(template.replace("法术列表模板","法术快速复制页").replace("{{内容}}","\n".join([spell.output_id_and_link for spell in big_spell_list])))
    """