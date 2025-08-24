import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
from 文件遍历 import walk_through_files


monster_file_list = [
"怪物图鉴2025"
]

source_tag: dict[str,str] = {
    "怪物图鉴2025" : "MM25",
}
source_priority: dict[str,int] = {
    "MM25": 0, # 最高优先级
}

class_list = ["天族","邪魔","亡灵","元素","泥怪","怪兽","野兽","类人","构装","龙类","异怪","妖精","植物"]

size_list = ["微型","小型","中型","大型","巨型","超巨型"]

#monster_conflict: dict[str,str] = {
    #"Feeblemind": "zzzzzzzzzFeeblemind",      
    #"Branding_Smite": "zzzzzzzzzBranding_Smite"  }

html_template_big = "../空白页模板/怪物大速查模板.htm"

class Monster:
    def __init__(self, content, chm_path="", source_tag="PHB14"):
        self.monster_name = ""
        self.monster_name_en = ""
        self.monster_id = ""
        self.monster_subline = ""
        self.monster_content = ""
        
        self.monster_classes = []
        self.monster_level = ""
        self.monster_verbal = False
        self.monster_somatic = False
        self.monster_material = False
        self.monster_material_sp = False
        self.monster_ritual = False
        self.monster_concentration = False
        self.monster_school = ""
        self.monster_source_tag = source_tag
        self.monster_source_priority = source_priority[source_tag]
        
        self.chm_path = chm_path
        self.legacy = False
        
        content = content.strip().replace("\r\n","").replace("\n","").replace("</H4>","</H4>\n").replace("<BR>","\n").replace("<BLOCKQUOTE","\n\n<BLOCKQUOTE").replace("<LI>","\n<LI> · ").replace("<P>","\n<P>")
        # 寻找id
        left = content.find("id=\"")+4
        right = content.find("\">",left)
        self.monster_id = content[left:right].strip()
        lines = BeautifulSoup(content, 'html.parser').get_text().splitlines()
        self.monster_name, self.monster_name_en = lines[0].split("｜")
        self.monster_name = self.monster_name.strip()
        self.monster_name_en = self.monster_name_en.strip()
        # 处理正文
        self.monster_subline = lines[1].strip()
        self.monster_content = "\n".join(lines[2:]).strip()
        print(self.monster_name+" · "+self.monster_subline)
        if "仪式" in self.monster_subline or "或仪式" in lines[2]:
            self.monster_ritual = True
        if "专注" in lines[5]:
            self.monster_concentration = True
        if "V" in lines[4]:
            self.monster_verbal = True
        if "S" in lines[4]:
            self.monster_somatic = True
        if "M" in lines[4]:
            self.monster_material = True
            if "价值" in lines[4] or "耗材" in lines[4] or "消耗" in lines[4]:
                self.monster_material_sp = True
        if "戏法" in self.monster_subline:
            self.monster_level = "戏法(零环)"
        elif "环" in self.monster_subline:
            for level in ["一环","二环","三环","四环","五环","六环","七环","八环","九环"]:
                if level in self.monster_subline:
                    self.monster_level = level
                    break
        else:
            print(id_and_link + " 解析出错！")
        
        for school in ["防护","咒法","预言","惑控","塑能","幻术","死灵","变化"]:
            if school in self.monster_subline:
                self.monster_school = school
                break
        for _class in class_list:
            if _class in self.monster_subline:
                self.monster_classes.append(_class)
        if "邪术师" in self.monster_subline:
            self.monster_classes.append("魔契师")
        if len(self.monster_classes) == 0:  # 如果没有匹配到任何职业
            self.monster_classes.append("其他")
                
    def output_id_and_link(self,_class="万法大全") -> str:
        display_name = self.monster_name+self.monster_name_en
        
          # 职业判断逻辑显示学派
        if _class in ["法师"]:
            display_name = self.monster_school+" - "+display_name

        # if self.monster_ritual and _class in ["法师","吟游诗人","牧师","德鲁伊","奇械师", "万法大全"]:
        
        if self.legacy:
            id_and_link = "<a class=\"legacy\" href=\""+self.chm_path+"#"+self.monster_id+"\">"+display_name+"</a>"
        else:
            id_and_link = "<a href=\""+self.chm_path+"#"+self.monster_id+"\">"+display_name+"</a>"
        
        if _class == "万法大全":
            tags = [
                self.monster_school,
                " ".join(self.monster_classes),
                self.monster_level,
                self.monster_source_tag
            ]
            if self.monster_verbal:
                tags.append("言语")
            if self.monster_somatic:
                tags.append("姿势")
            if self.monster_material:
                tags.append("材料")
            if self.monster_material_sp:
                tags.append("价耗")
            if self.monster_ritual:
                tags.append("仪式")
            if self.monster_concentration:
                tags.append("专注")
            labels = [
                id_and_link, #法术名（带链接）
                self.monster_level, #法术环阶
                self.monster_school, #法术学派
                " ".join([short_cut[_class] for _class in self.monster_classes]), #法术职业简写
                "V" if self.monster_verbal else "×", #言语成分
                "S" if self.monster_somatic else "×", #姿势成分
                "M*" if self.monster_material_sp else ("M" if self.monster_material else "×"), #材料成分
                "√" if self.monster_ritual else "×", #
                "√" if self.monster_concentration else "×", #专注
                self.monster_source_tag #来源
            ]
            id_and_link = "<TR tags=\"" +" ".join(tags)+"\" monster=\""+self.monster_name+self.monster_name_en+"\"><TD>"+"</TD><TD>".join(labels)+"</TD></TR>"
        elif self.monster_source_tag not in ["","PHB14","PHB24"]: #角标
            id_and_link += "<sup>"+self.monster_source_tag+"</sup>"
        return id_and_link
    
    def output_database(self) -> list[str]:
        output = [self.monster_name,self.monster_name_en,self.monster_source_tag,"法术",self.monster_subline,self.monster_content]
        return output

class_monster_list: dict[str, dict[str, list[monster]]] = {}
big_monster_list: dict[str, monster] = {}
big_monster_list_keys: list[str] = []

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
            monster = monster(content,chm_path,source)
            
            for _class in monster.monster_classes:
                if _class not in class_monster_list.keys():
                    class_monster_list[_class] = {}
                if monster.monster_level not in class_monster_list[_class].keys():
                    class_monster_list[_class][monster.monster_level] = []
                class_monster_list[_class][monster.monster_level].append(monster)
            
            if monster.monster_id in big_monster_list.keys():
                big_monster_list[monster.monster_id].legacy = True
                big_monster_list["zzzzzzzzz"+monster.monster_id] = big_monster_list[monster.monster_id]
                big_monster_list_keys.append("zzzzzzzzz"+monster.monster_id)
            elif monster.monster_id in monster_conflict.keys():#手动冲突检测
                new_id = monster_conflict[monster.monster_id]
                big_monster_list[new_id] = monster
                big_monster_list_keys.append(new_id)
                monster.legacy = True  # 标记为过时
            else:
                big_monster_list[monster.monster_id] = monster
                big_monster_list_keys.append(monster.monster_id)
            
            big_monster_list[monster.monster_id] = monster
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
        class_monster_list[c] = {}
        for level in level_list:
            class_monster_list[c][level]: list[str] = []
    for file in monster_file_list:
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
            if len(class_monster_list[c][level]) != 0:
                # 去legacy，排序并输出
                sorted_monsters = [monster for monster in class_monster_list[c][level] if not monster.legacy or c == "奇械师"] # 忽略legacy内容
                sorted_monsters = sorted(sorted_monsters,key=lambda x: (x.monster_source_priority,x.monster_name_en))# 排序：来源优先，法术名次优先
                contents.append("<h2>"+level+"</h2>\n<p>"+"<br>\n".join([monster.output_id_and_link(c) for monster in sorted_monsters])+"</p>")
        with open("../速查/法术速查/"+c+"法术速查.html",mode="w",encoding="gbk") as _f:
            _f.write(template.replace("法术列表模板",c+"法术列表").replace("{{内容}}","\n".join(contents)))

    # 生成速查大表
    big_monster_list_keys.sort()
    print("已发现合计 "+str(len(big_monster_list_keys))+" 个法术。")
    with open("../速查/法术速查/5E万法大全.html",mode="w",encoding="gbk") as _f:
        _f.write(template_big.replace("法术列表模板","5E万法大全").replace("{{内容}}","\n".join([big_monster_list[monster_id].output_id_and_link(_class="万法大全") for monster_id in big_monster_list_keys])))
    

    """
    template = ""
    with open("../空白页模板/法术快速复制页模板.htm",mode="r",encoding="gbk") as _f:
        template = _f.read()
    # Workbook
    wb = Workbook()
    ws = wb.create_sheet(title="万法大全")
    for monster_id in big_monster_list_keys:
        ws.append(big_monster_list[monster_id].output_database())
    wb.save("../速查/法术速查/5E万法大全.xlsx")
    
    with open("./Generated/法术快速复制页.html",mode="w",encoding="gbk") as _f:
        _f.write(template.replace("法术列表模板","法术快速复制页").replace("{{内容}}","\n".join([monster.output_id_and_link for monster in big_monster_list])))
    """