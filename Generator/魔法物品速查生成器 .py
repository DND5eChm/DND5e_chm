import os
import re
from bs4 import BeautifulSoup
from 文件遍历 import walk_through_files


# ========= 输入文件 =========
item_file_list = [
    "城主指南2024/7.宝藏/魔法物品详述",
    # 自行补充
]


# ========= 来源 =========
source_tag = {
    "城主指南2024": "DMG24",
}


# ========= 基础分类 =========
rarity_list = ["普通","非普通","珍稀","极珍稀","传说","神器","多种稀有度"]
category_list = ["护甲","武器","戒指","权杖","卷轴","法杖","魔杖","药水","奇物"]


# ========= 子类型映射 =========
subtype_map = {

}


# ========= 未映射 =========
unmapped_subtypes = set()


# ========= 工具 =========
def split_subtypes(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"[或、/]", text) if p.strip()]


# ========= 类 =========
class MagicItem:
    def __init__(self, content, chm_path="", source="未知"):
        self.name = ""
        self.name_en = ""
        self.item_id = ""

        self.category = "其他"
        self.rarity = "普通"
        self.attunement = "否"

        self.subtypes = []
        self.subtypes_mapped = []

        self.source = source
        self.chm_path = chm_path

        soup = BeautifulSoup(content, "html.parser")

        # ID
        self.item_id = soup.find("h6")["id"]

        # 名称
        title = soup.find("h6").get_text(strip=True)
        parts = title.split(" ", 1)
        self.name = parts[0]
        if len(parts) > 1:
            self.name_en = parts[1]

        # 副行
        subline = soup.find("p").get_text(" ", strip=True)

        # 稀有度
        for r in rarity_list:
            if r in subline:
                self.rarity = r
                break

        # 类别 + 子类型
        for c in category_list:
            if c in subline:
                self.category = c

                match = re.search(rf"{c}（([^）]+)）", subline)
                if match:
                    raw = match.group(1)
                    self.subtypes = split_subtypes(raw)

                    for sub in self.subtypes:
                        if sub in subtype_map:
                            mapped = subtype_map[sub]
                        else:
                            mapped = sub
                            unmapped_subtypes.add(sub)

                        if mapped not in self.subtypes_mapped:
                            self.subtypes_mapped.append(mapped)

                break

        # 同调
        if "需同调" in subline:
            if "需同调（" in subline:
                self.attunement = "特殊"
            else:
                self.attunement = "是"
        else:
            self.attunement = "否"

    def to_row(self):
        tags = [
            self.rarity,
            self.category,
            self.attunement,
            self.source
        ]

        tags.extend(self.subtypes_mapped)

        name_display = self.name + " " + self.name_en

        category_display = self.category
        if self.subtypes:
            category_display += f"（{'/'.join(self.subtypes)}）"

        return (
            f'<TR tags="{" ".join(tags)}" item="{name_display}">\n'
            f'<TD><a href="{self.chm_path}#{self.item_id}">{name_display}</a></TD>\n'
            f'<TD>{self.rarity}</TD>\n'
            f'<TD>{category_display}</TD>\n'
            f'<TD>{self.attunement}</TD>\n'
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

    chm_path = file_path.replace("\\","/").split("DND5e_chm/")[1]

    parts = chm_path.split("/")
    book = parts[1]
    source = source_tag.get(book, book)

    print("解析来源:", source)

    for content in contents:
        try:
            item = MagicItem(content, chm_path, source)
            big_item_dict[item.item_id] = item
        except Exception:
            print("解析失败:", content[:50])


# ========= 运行 =========
if __name__ == "__main__":

    for file in item_file_list:
        walk_through_files(process_file, file)

    print("\n总计物品:", len(big_item_dict))

    # ===== 读取模板 =====
    with open(template_path, "r", encoding="gbk") as f:
        template = f.read()

    # ===== 生成内容 =====
    rows = [item.to_row() for item in big_item_dict.values()]
    html = template.replace("{{内容}}", "\n".join(rows))

    # ===== 写入输出 =====
    with open(output_path, "w", encoding="gbk") as f:
        f.write(html)

    print("\n已生成:", output_path)

    # ===== 未映射输出 =====
    print("\n====== 未映射子类型 ======")
    if not unmapped_subtypes:
        print("没有未映射项 👍")
    else:
        for sub in sorted(unmapped_subtypes):
            print(sub)