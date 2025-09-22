import os
from bs4 import BeautifulSoup
from openpyxl import Workbook
from 文件遍历 import walk_through_files


monster_file_list = [
    "怪物图鉴2025",
]

source_tag: dict[str,str] = {
    "怪物图鉴2025": "MM25",
}
source_priority: dict[str,int] = {
    "MM25": 0, # 最高优先级
}

size_list = ["微型", "小型", "中型", "大型", "巨型", "超巨型"]
type_list = ["异怪", "野兽", "天族", "构装", "龙类", "元素", "妖精", "邪魔", "巨人", "类人", "怪兽", "泥怪", "植物", "亡灵"]
cr_list = ["0", "1/8", "1/4", "1/2"] + [str(i) for i in range(1, 30)]

html_template_big = "../空白页模板/怪物大速查模板.htm"

class Monster:
    def __init__(self, content, chm_path="", source_tag="MM25"):
        self.monster_name = ""
        self.monster_id = ""
        self.monster_subline = ""
        self.monster_size = ""
        self.monster_type = ""
        self.monster_tag = ""
        self.monster_cr = ""

        self.monster_source_tag = source_tag
        self.monster_source_priority = source_priority[source_tag]
        
        self.chm_path = chm_path
        self.legacy = False
        
        content = content.strip().replace("\r\n","").replace("\n","").replace("</H5>","</H5>\n").replace("<BR>","\n").replace("<P>","\n<P>")
        # 寻找id
        left = content.find("id=\"")+4
        right = content.find("\">",left)
        self.monster_id = content[left:right].strip()
        lines = BeautifulSoup(content, "html.parser").get_text().splitlines()
        # 处理正文
        self.monster_name = lines[0].strip()
        self.monster_subline = lines[1].strip()
        for size in ["微型", "小型", "中型", "大型", "巨型", "超巨型"]:
            if size in self.monster_subline:
                self.monster_size = size
                break
        for type in ["异怪", "野兽", "天族", "构装", "龙类", "元素", "妖精", "邪魔", "巨人", "类人", "怪兽", "泥怪", "植物", "亡灵"]:
            if type in self.monster_subline:
                self.monster_type = type
                break
        if "（" "）" in lines[1]:
                left = content.find("（")+4
                right = content.find("）",left)
                self.monster_tag = content[left:right].strip()
        
        left = content.find("CR </strong>" or "CR </b>" or "挑战等级 </b>" or "挑战等级 </strong>" )+4
        right = content.find("（",left)
        
    def output_id_and_link(self,_class="万兽大全") -> str:
        display_name = self.monster_name

        id_and_link = "<a href=\""+self.chm_path+"#"+self.monster_id+"\">"+display_name+"</a>"

        if _class == "万兽大全":
            tags = [
                self.monster_size,
                self.monster_type,
                self.monster_tag,
                self.monster_cr,
                self.monster_source_tag,
            ]
            labels = [
                id_and_link,
                self.monster_type,
                self.monster_tag,
                self.monster_source_tag
            ]
            id_and_link = "<TR tags=\"" +" ".join(tags)+"\" monster=\""+self.monster_name+"\"><TD>"+"</TD><TD>".join(labels)+"</TD></TR>"+ "<sup>"+self.monster_source_tag+"</sup>"
        return id_and_link
    
    def output_database(self) -> list[str]:
        output = [self.monster_name,self.monster_source_tag,"怪物",self.monster_subline]
        return output

big_monster_list: dict[str, Monster] = {}
big_monster_list_keys: list[str] = []

def process_file(file_path: str,file_name: str):
    data = ""
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gbk") as _f:
        data = _f.read()
    data = data[data.find("<body>")+6:data.find("</body>")]
    contents = [("<div class=\"stat-block\"" + content).strip() for content in data.split("<div class=\"stat-block\"") if content.strip() != ""]
    id_and_link = ""
    source = ""
    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]
    """
    for book in source_tag.keys():
        if book in chm_path:
            source = source_tag[book]
            break
    """
    book = chm_path.split("/")[0]
    if book in source_tag.keys():
        source = source_tag[book]
    else:
        source = book
    # 获取资源
    for content in contents:
        try:
            # 获取法术
            monster = Monster(content,chm_path,source)
            
            big_monster_list[monster.monster_id] = monster
            big_monster_list_keys.append(monster.monster_id)

        except:
            if len(content) > 40:
                print(content[:40]+"... 解析出错")
            else:
                print(content+" 解析出错")

if __name__ == "__main__":

    target_folder = os.path.exists("./Generated")
    if not target_folder:
        os.makedirs("./Generated")

    # 生成速查
    template_big = ""

    with open(html_template_big,mode="r",encoding="gbk") as _f:
        template_big = _f.read()

    # 生成速查大表
    big_monster_list_keys.sort()
    print("已发现合计 "+str(len(big_monster_list_keys))+" 个怪物。")
    with open("../速查/5E万兽大全.html",mode="w",encoding="gbk") as _f:
        _f.write(template_big.replace("5E万兽大全").replace("{{内容}}","\n".join([big_monster_list[monster_id].output_id_and_link(_class="万兽大全") for monster_id in big_monster_list_keys])))
    