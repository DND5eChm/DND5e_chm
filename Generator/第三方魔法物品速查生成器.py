import os
import re
from bs4 import BeautifulSoup
from 文件遍历 import walk_through_files


# ========= 输入 =========
item_file_list = [
    "第三方/狮鹫的鞍中珍宝Ⅱ/魔法物品",
    "第三方/歪曲之月/附录B",
    "第三方/惊奇单次冒险/魔法物品.htm",
    "第三方/拳斗士/魔法物品.htm",
    "第三方/瓦尔达的秘密尖塔/魔法物品.htm",
]

# ========= 模板 / 输出 =========
template_path = "../空白页模板/合作方道具大速查模板.htm"
output_path = "../速查/合作万器大全.htm"


# ========= 来源 =========
source_tag = {
    "狮鹫的鞍中珍宝Ⅱ": "狮鹫Ⅱ",
    "拳斗士": "拳斗士",
    "惊奇单次冒险": "惊奇一发",
    "歪曲之月": "歪月",
    "瓦尔达的秘密尖塔": "尖塔",
}


# ========= 基础 =========
rarity_list = ["普通","非普通","珍稀","极珍稀","传说","神器","多种稀有度"]
category_list = ["护甲","武器","戒指","权杖","卷轴","法杖","魔杖","药水","奇物"]
rarity_tag_map = {
    "非普通": "非普",
    "极珍稀": "极珍",
    "多种稀有度": "多种"
}


# ========= 子类别映射 =========
subtype_map = {
    "任意中甲或重甲，兽皮甲除外": ["链甲衫","鳞甲","半身板甲","重甲"],
    "任意简易或军用": ["简易武器","军用武器"],
    "任意简易武器或军用武器": ["简易武器","军用武器"],
    "任意弹药或近战武器": ["弹药","近战武器"],
    "任意剑": ["长柄刀","巨剑","长剑","刺剑","弯刀","短剑"], 
    "任意弓": ["长弓","短弓"], 
    "任意弩": ["手弩","轻弩","重弩"], 
    "任意弓或弩" : ["长弓","短弓","手弩","轻弩","重弩"],
    "任意斧": ["战斧","巨斧","戟","手斧"], 
    "箭或弩矢":["箭矢","弩矢"],

}


# ========= 同调映射 =========
attunement_map = {
"缺失手或臂的生物": ["缺失手","缺失臂"],
"缺失手、臂或腿的生物": ["缺失手","缺失臂","缺失腿"],
"缺失一眼的生物": ["缺失一眼"],
}


# ========= 白名单 =========
subtype_whitelist = set("""
短棒 匕首 巨棒 手斧 标枪 轻锤 硬头锤 长棍 镰刀 矛
飞镖 轻弩 短弓 投石索
战斧 链枷 长柄刀 巨斧 巨剑 戟 骑枪 长剑 巨锤 钉头锤 长矛 刺剑 弯刀 短剑 三叉戟 战镐 战锤 鞭
吹箭筒 手弩 重弩 长弓 火铳 手铳
手爪 指虎 推匕
简易武器 军用武器 弹药 盾牌 近战武器 
轻甲 中甲 重甲 皮甲 链甲 胸甲 链甲衫 镶钉皮甲 鳞甲 兽皮甲 半身板甲 板条甲 板甲
金属军用武器 
匕首与短剑 链甲衫与半身板甲
坐骑用重甲
箭矢 弩矢
没有特殊和双手词条的近战武器
中甲（兽皮甲除外）
""".split())

attunement_whitelist = set("""
吟游诗人 牧师 德鲁伊 圣武士 游侠
术士 法师 魔契师 奇械师 拳斗士
野蛮人 武僧 战士 游荡者 施法者 
武器选择的生物 与矮人腰带维持同调的生物
半精灵 妖精 小型类人 精灵 矮人
中立阵营的生物 善良阵营的施法者 善良阵营的生物
感知不小于13的生物 敏捷不小于17的生物 智力不小于17的生物
斧认定有价值的生物
缺失一眼 缺失手 缺失腿 缺失臂
善良阵营的龙裔 中立阵营的龙裔 邪恶阵营的龙裔 非守序阵营的龙裔
""".split())


# ========= 未映射 =========
unmapped_subtypes = set()
unmapped_attunement = set()


# ========= 工具 =========
def clean_text(t):
    return t.replace("\u3000", " ").replace("\xa0", " ").strip()


def split_multi(text):
    return [t.strip() for t in re.split(r"[，,、/或]", text) if t.strip()]


# ========= 子类别 =========
def normalize_subtypes(text):
    if not text:
        return []

    text = clean_text(text)

    if text in subtype_map:
        return subtype_map[text]

    parts = split_multi(text)

    result = []
    for p in parts:
        p = p.replace("任意", "").strip()
        if p:
            result.append(p)

    return result


# ========= 同调 =========
def normalize_attunement(text):
    if not text:
        return []

    text = clean_text(text)
    
    # 移除前导的“需”和两侧括号
    text = text.replace("需", "").strip("（） ")
    
    # 优化：只移除字符串末尾的“同调”
    # 比如 "矮人同调" -> "矮人"
    # 但 "与...同调的生物" 保持不变
    text = re.sub(r"同调$", "", text)

    # ===== 精确映射 =====
    if text in attunement_map:
        return attunement_map[text]

    # ===== 子串映射 =====
    for k, v in attunement_map.items():
        if k in text:
            return v

    # ===== fallback =====
    # 这里处理“或是”、“或”等连接词
    parts = [p.strip() for p in re.split(r"[，,、/或]|或是", text) if p.strip()]
    return parts


# ========= 类 =========
class MagicItem:
    def __init__(self, content, chm_path="", source="未知"):

        self.name = ""
        self.name_en = ""
        self.item_id = ""

        self.category = "其他"
        self.rarity = "普通"
        self.rarity_tag = "普通"

        self.attunement = "否"
        self.attune_conditions = []
        self.subtypes = []

        self.source = source
        self.chm_path = chm_path

        soup = BeautifulSoup(content, "html.parser")

        self.item_id = soup.find("h6")["id"]

        title = soup.find("h6").get_text(strip=True)
        parts = title.split(" ", 1)
        self.name = parts[0]
        self.name_en = parts[1] if len(parts) > 1 else ""

        p = soup.find("p")
        em = p.find("em")

        subline = em.get_text(" ", strip=True) if em else p.get_text(" ", strip=True)
        subline = clean_text(re.sub(r"\s+", " ", subline))

        # ========= 稀有度 =========
        for r in sorted(rarity_list, key=len, reverse=True):
            if r in subline:
                self.rarity = r
                self.rarity_tag = rarity_tag_map.get(r, r)
                break

        # ========= 类别 =========
        for c in category_list:
            if c in subline:
                self.category = c

                match = re.search(rf"{c}（([^）]+)）", subline)
                if match:
                    raw = match.group(1)
                    subs = normalize_subtypes(raw)

                    for s in subs:
                        if s not in self.subtypes:
                            self.subtypes.append(s)
                        if s not in subtype_whitelist:
                            unmapped_subtypes.add(s)
                break

        # ========= 同调（精准提取版） =========
        self.attunement = "否"
        self.attune_conditions = []

        m = re.search(r"（需(.+?)同调）", subline)

        if m:
            raw = clean_text(m.group(1))  # ⚠️ 这里已经是“XX”本体

            self.attunement = "是"

            # 如果不是空，说明是特殊同调
            if raw.strip():
                self.attunement = "特殊"

                conds = normalize_attunement(raw)

                for c in conds:
                    c = clean_text(c)

                    if not c:
                        continue

                    if c not in self.attune_conditions:
                        self.attune_conditions.append(c)

                    if c not in attunement_whitelist:
                        unmapped_attunement.add(c)

    def to_row(self):

        tags = [
            self.rarity_tag,
            self.category,
            self.attunement,
            self.source
        ] + self.subtypes + self.attune_conditions

        name_display = self.name + self.name_en

        return (
            f'<TR tags="{" ".join(tags)}" item="{name_display}">\n'
            f'<TD><a href="{self.chm_path}#{self.item_id}">{name_display}</a></TD>\n'
            f'<TD>{self.rarity}</TD>\n'
            f'<TD>{self.category}</TD>\n'
            f'<TD>{" / ".join(self.subtypes)}</TD>\n'
            f'<TD>{self.attunement}</TD>\n'
            f'<TD>{" / ".join(self.attune_conditions)}</TD>\n'
            f'<TD>{self.source}</TD>\n'
            f'</TR>'
        )


# ========= 主流程 =========
big_item_dict = {}


def process_file(file_path, file_name):

    with open(file_path, "r", encoding="gbk") as f:
        data = f.read()

    body = data[data.find("<body>")+6:data.find("</body>")]
    contents = [("<H6" + c) for c in body.split("<H6")[1:]]

    chm_path = file_path.replace("\\","/")

    if "DND5e_chm/" in chm_path:
        chm_path = chm_path.split("DND5e_chm/")[1]

    parts = chm_path.split("/")
    book = parts[0]

    if book in ["第三方"]:
        book = parts[1]
        source = source_tag.get(book, book)
    elif book in source_tag:
        source = source_tag[book]
    else:
        source = book

    print("来源:", source)

    for c in contents:
        try:
            item = MagicItem(c, chm_path, source)
            big_item_dict[item.item_id] = item
        except Exception:
            print("解析失败:", c[:50])


# ========= 运行 =========
if __name__ == "__main__":

    for f in item_file_list:
        walk_through_files(process_file, f)

    print("总计:", len(big_item_dict))

    with open(template_path, "r", encoding="gbk") as f:
        tpl = f.read()

    html = tpl.replace(
        "{{内容}}",
        "\n".join(
            i.to_row()
            for i in sorted(
                big_item_dict.values(),
                key=lambda x: x.name_en.lower()  # 按英文名首字母排序
            )
        )
    )

    with open(output_path, "w", encoding="gbk") as f:
        f.write(html)

    print("输出完成:", output_path)

    print("\n====== 未映射子类别 ======")
    for x in sorted(unmapped_subtypes):
        print(x)

    print("\n====== 未映射同调条件 ======")
    for x in sorted(unmapped_attunement):
        print(x)