import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
from 文件遍历 import walk_through_files


spell_file_list = [
    "第三方/塔尔多雷/玩家选项/新法术详述.htm",
    "第三方/鬼魅幽谷/艾弗瑞斯之巢/附录A/法术.htm",
    "第三方/鬼魅幽谷/玩家包/法术.htm",
    "第三方/德拉肯海姆/法术详述.htm",
    "第三方/谦卑林/新法术详述.htm",
    "第三方/谦卑林故事集/新法术.htm",
    "第三方/黯潮之书/法术/法术详述.htm",
    "第三方/邪狱使/邪狱使法术.htm",
    "第三方/胧忆岛/法术.htm",
    "第三方/瓦尔达的秘密尖塔/法术.htm",
    "第三方/瓦尔达的秘密尖塔/铳士/法术.htm",
    "第三方/歪曲之月/第七章/法术详述.htm",
    "第三方/火炬光下的克苏鲁/第四章/法术详述.htm",
]

source_tag: dict[str,str] = {
    "塔尔多雷": "塔尔多雷",
    "艾弗瑞斯之巢": "艾巢",
    "玩家包": "鬼谷14",
    "德拉肯海姆": "德城",
    "谦卑林": "谦战",
    "谦卑林故事集": "谦故",
    "黯潮之书": "黯潮",
    "邪狱使": "邪狱使",
    "胧忆岛": "胧忆岛",
    "瓦尔达的秘密尖塔": "尖塔",
    "铳士": "铳士",
    "歪曲之月": "歪月",
    "火炬光下的克苏鲁": "克苏鲁",
}
source_priority: dict[str,int] = {
    "溟渊": 0,
    "艾巢": 2,
    "鬼谷14": 1,
    "德城": 3,
    "谦战": 4,
    "谦故": 5,
    "黯潮": 6,
    "邪狱使": 7,
    "胧忆岛": 8,
    "尖塔": 10,
    "铳士": 9,
    "歪月": 11,
    "克苏鲁": 12,
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
    "无职" : "无"
}

class_list = ["吟游诗人","牧师","德鲁伊","圣武士","游侠","术士","法师","魔契师","奇械师"]

level_list = ["戏法","一环","二环","三环","四环","五环","六环","七环","八环","九环"]

html_template_big = "../空白页模板/合作方法术大速查模板.htm"

class Spell:
    def __init__(self, content, chm_path="", source_tag="PHB14", order=0):
        self.spell_name = ""
        self.spell_name_en = ""
        self.spell_id = ""
        self.spell_subline = ""
        self.spell_content = ""
        self.parse_order = order
        self.spell_classes = []
        self.spell_level = ""
        self.spell_action = ""
        self.spell_verbal = False
        self.spell_somatic = False
        self.spell_material = False
        self.spell_material_sp = False
        self.spell_ritual = False
        self.spell_concentration = False
        self.spell_school = ""
        self.spell_source_tag = source_tag
        self.spell_source_priority = 99
        if source_tag in source_priority.keys():
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
        if "反应" in lines[2]:
            self.spell_action = "反应"
        elif "附赠" in lines[2]:
            self.spell_action = "附赠"
        elif "动作" in lines[2]:
            self.spell_action = "动作"
        else: self.spell_action = "其他"
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
            self.spell_level = "戏法"
        elif "环" in self.spell_subline:
            for level in ["一环","二环","三环","四环","五环","六环","七环","八环","九环"]:
                if level in self.spell_subline:
                    self.spell_level = level
                    break
        else:
            print(self.spell_name + " 解析出错！未能在["+self.spell_subline+"]行找到环阶信息")
        
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
            self.spell_classes.append("无职")
                
    def output_id_and_link(self,_class="合作方万法大全") -> str:
        display_name = self.spell_name+self.spell_name_en
        
          # 职业判断逻辑显示学派
        if _class in ["法师"]:
            display_name = self.spell_school+" - "+display_name

        # if self.spell_ritual and _class in ["法师","吟游诗人","牧师","德鲁伊","奇械师", "合作方万法大全"]:
        
        if self.legacy:
            id_and_link = "<a class=\"legacy\" href=\""+self.chm_path+"#"+self.spell_id+"\">"+display_name+"</a>"
        else:
            id_and_link = "<a href=\""+self.chm_path+"#"+self.spell_id+"\">"+display_name+"</a>"
        
        if _class == "合作方万法大全":
            tags = [
                self.spell_school,
                self.spell_action,
                " ".join(self.spell_classes),
                self.spell_level,
                self.spell_source_tag
            ]
            if self.spell_verbal:
                tags.append("言语")
            else:tags.append("非言")
            if self.spell_somatic:
                tags.append("姿势")
            else:tags.append("非姿")
            if self.spell_material:
                tags.append("材料")
            else:tags.append("非材")
            if self.spell_material_sp:
                tags.append("价耗")
            elif self.spell_material:
                tags.append("无特")
            if self.spell_ritual:
                tags.append("仪式")
            else:tags.append("非仪")
            if self.spell_concentration:
                tags.append("专注")
            else:tags.append("非专")
            labels = [
                id_and_link, #法术名（带链接）
                self.spell_level, #法术环阶
                self.spell_school, #法术学派
                " ".join([short_cut[_class] for _class in self.spell_classes]), #法术职业简写
                self.spell_action,
                "V" if self.spell_verbal else "×", #言语成分
                "S" if self.spell_somatic else "×", #姿势成分
                "M*" if self.spell_material_sp else ("M" if self.spell_material else "×"), #材料成分
                "√" if self.spell_ritual else "×", #
                "√" if self.spell_concentration else "×", #专注
                self.spell_source_tag #来源
            ]
            id_and_link = "<TR tags=\"" +" ".join(tags)+"\" spell=\""+self.spell_name+self.spell_name_en+"\">\r\n<TD>"+"</TD>\r\n<TD>".join(labels)+"</TD>\r\n</TR>"#换行增强可视性
        elif self.spell_source_tag not in ["","PHB14","PHB24"]: #角标
            id_and_link += "<sup>"+self.spell_source_tag+"</sup>"
        return id_and_link
    
    def output_database(self) -> list[str]:
        output = [self.spell_name,self.spell_name_en,self.spell_source_tag,"法术",self.spell_subline,self.spell_content]
        return output

big_spell_list: dict[str, Spell] = {}
big_spell_list_keys: list[str] = []

parse_counter = 0

def process_file(file_path: str,file_name: str):
    data = ""
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gbk") as _f:
        data = _f.read()
    data = data[data.find("<body>")+6:data.find("</body>")]
    contents = [("<H4" + content).strip() for content in data.split("<H4")[1:] if content.strip() != ""]

    id_and_link = ""
    source = ""
    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]
    '''
    for book in source_tag.keys():
        if book in chm_path:
            source = source_tag[book]
            break
    '''
    parts = chm_path.split("/")
    book = parts[1]

    # 瓦尔达特殊处理
    if book == "瓦尔达的秘密尖塔":
        if len(parts) >= 4 and parts[2] == "铳士":
            source = "铳士"
        else:
            source = source_tag.get(book, book)

    # 其他类似结构（鬼魅幽谷等）
    elif book in ["鬼魅幽谷"]:
        if len(parts) >= 3:
            sub = parts[2]
            source = source_tag.get(sub, sub)
        else:
            source = source_tag.get(book, book)

    # 普通来源
    elif book in source_tag:
        source = source_tag[book]

    else:
        source = book

    print("开始寻找 "+book+" 内的资源。")
    # 获取资源
    for content in contents:
        #try:
            # 获取法术
            global parse_counter
            parse_counter += 1
            spell = Spell(content, chm_path, source, order=parse_counter)
    
            key = f"{spell.spell_id}__{spell.spell_source_tag}"
            big_spell_list[key] = spell
            big_spell_list_keys.append(key)
            
        #except:
        #    if len(content) > 100:
        #        print(content[:100]+"... 解析出错")
        #    else:
        #        print(content+" 解析出错")

if __name__ == "__main__":

    target_folder = os.path.exists("./Generated")
    if not target_folder:
        os.makedirs("./Generated")

    for file in spell_file_list:
        walk_through_files(process_file,file)
    
    from collections import defaultdict

    # 1. 按 spell_id 分组
    spell_groups: dict[str, list[Spell]] = defaultdict(list)

    for spell in big_spell_list.values():
        spell_groups[spell.spell_id].append(spell)

# 2. 每组按来源优先级排序，标记 legacy
    big_spell_list.clear()
    big_spell_list_keys.clear()

    for spell_id, spells in spell_groups.items():
     # 按解析顺序，后出现的在前
        spells.sort(key=lambda s: s.parse_order, reverse=True)

        for i, spell in enumerate(spells):
            spell.legacy = (i != 0)

            key = spell.spell_id
            if spell.legacy:
                key = f"zzzzzzzzz{spell.spell_id}__{spell.spell_source_tag}"
            else:
                key = f"{spell.spell_id}__{spell.spell_source_tag}"

            big_spell_list[key] = spell
            big_spell_list_keys.append(key)

    # 生成速查
    template_big = ""
    
    with open(html_template_big,mode="r",encoding="gbk") as _f:
        template_big = _f.read()

    # 生成速查大表
    big_spell_list_keys.sort()
    print("已发现合计 "+str(len(big_spell_list_keys))+" 个法术。")
    with open("../速查/法术速查/合作方万法大全.html",mode="w",encoding="gbk") as _f:
        _f.write(template_big.replace("法术列表模板","合作方万法大全").replace("{{内容}}","\n".join([big_spell_list[spell_id].output_id_and_link(_class="合作方万法大全") for spell_id in big_spell_list_keys])))
    

    """
    template = ""
    with open("../空白页模板/法术快速复制页模板.htm",mode="r",encoding="gbk") as _f:
        template = _f.read()
    # Workbook
    wb = Workbook()
    ws = wb.create_sheet(title="合作方万法大全")
    for spell_id in big_spell_list_keys:
        ws.append(big_spell_list[spell_id].output_database())
    wb.save("../速查/法术速查/合作方万法大全.xlsx")
    
    with open("./Generated/法术快速复制页.html",mode="w",encoding="gbk") as _f:
        _f.write(template.replace("法术列表模板","法术快速复制页").replace("{{内容}}","\n".join([spell.output_id_and_link for spell in big_spell_list])))
    """