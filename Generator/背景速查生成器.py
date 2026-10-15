import re
from bs4 import BeautifulSoup
from 文件遍历 import walk_through_files


# ============================================================
# 输入
# ============================================================

background_file_list = [
    "玩家手册2024/角色起源/背景",
    "被遗忘的国度/费伦英雄/第一章/背景",
]


# ============================================================
# 模板 / 输出
# ============================================================

template_path = "../空白页模板/背景大速查模板.htm"
output_path = "../速查/背景大速查表.htm"


# ============================================================
# 来源
# ============================================================

source_tag = {
    "玩家手册2024": "PHB24",
    "费伦英雄": "FR",
}


# ============================================================
# 基础数据
# ============================================================

ability_list = [
    "力量",
    "敏捷",
    "体质",
    "感知",
    "智力",
    "魅力",
]

skill_list = [
    "特技",
    "驯兽",
    "奥秘",
    "运动",
    "欺瞒",
    "历史",
    "洞悉",
    "威吓",
    "调查",
    "医药",
    "自然",
    "察觉",
    "表演",
    "游说",
    "宗教",
    "巧手",
    "隐匿",
    "求生",
]


# ============================================================
# 工具
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def html_escape(text):
    return (
        text
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def normalize_id(text):
    text = clean_text(text)

    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_'’-]", "_", text)
    text = re.sub(r"_+", "_", text)

    return text.strip("_")


def get_source(file_path):

    path = file_path.replace("\\", "/")

    if "DND5e_chm/" in path:
        path = path.split("DND5e_chm/", 1)[1]

    parts = path.split("/")

    if not parts:
        return "未知"

    book = parts[0]

    if book == "被遗忘的国度":
        if len(parts) > 1:
            book = parts[1]

    return source_tag.get(book, book)


def get_chm_path(file_path):

    chm_path = file_path.replace("\\", "/")

    if "DND5e_chm/" in chm_path:
        chm_path = chm_path.split("DND5e_chm/", 1)[1]

    return chm_path


# ============================================================
# 名称
# ============================================================

def get_background_title(h3):

    title = clean_text(
        h3.get_text(" ", strip=True)
    )

    # 兼容：
    #
    # 流浪者Wayfarer
    # 水手 Sailor
    # 艺人 Entertainer
    #
    # 英文名从第一个英文字符开始

    match = re.search(
        r"([A-Za-z][A-Za-z0-9 &'’'_-]*)$",
        title
    )

    if match:
        name_en = clean_text(match.group(1))
        name = clean_text(title[:match.start()])
    else:
        name = title
        name_en = ""

    return name, name_en


def get_id(h3, name_en):

    item_id = h3.get("id")

    if item_id:
        return item_id

    return normalize_id(name_en)


# ============================================================
# 提取背景字段
# ============================================================

def get_background_fields(h3):
    p = h3.find_next("p")
    if not p:
        return {}

    html = str(p)

    pattern = re.compile(
        r"<(?:b|strong)\s*>\s*"
        r"(属性值|专长|技能熟练|工具熟练|装备)"
        r"\s*[：:]?\s*"
        r"</(?:b|strong)>"
        r"(.*?)"
        r"(?=<(?:b|strong)\s*>\s*"
        r"(?:属性值|专长|技能熟练|工具熟练|装备)"
        r"\s*[：:]?\s*</(?:b|strong)>|$)",
        re.I | re.S
    )

    fields = {}

    for match in pattern.finditer(html):
        label = match.group(1)
        value = match.group(2)

        value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
        value = BeautifulSoup(value, "html.parser").get_text(
            " ", strip=True
        )
        value = clean_text(value)

        fields[label] = value

    return fields

    # --------------------------------------------------------
    # 注意：
    #
    # 有的页面使用 <b>
    # 有的页面使用 <STRONG>
    #
    # 所以这里统一识别：
    #
    # <b>属性值：</b>
    # <strong>专长：</strong>
    # --------------------------------------------------------

    pattern = re.compile(
        r"<(?:b|strong)\s*>\s*"
        r"(属性值|专长|技能熟练|工具熟练)"
        r"\s*[：:]?\s*"
        r"</(?:b|strong)>"
        r"(.*?)"
        r"(?=<(?:b|strong)\s*>\s*"
        r"(?:属性值|专长|技能熟练|工具熟练)"
        r"\s*[：:]?\s*</(?:b|strong)>|$)",
        re.I | re.S
    )

    html = str(p)

    matches = pattern.findall(html)

    for label, value in matches:

        soup = BeautifulSoup(
            value,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        fields[label] = clean_text(text)

    return fields


# ============================================================
# 属性
# ============================================================

def get_ability(text):

    if not text:
        return "无"

    text = clean_text(text)

    # 任意属性
    choice_patterns = [
        r"任意",
        r"一项属性",
        r"另一项属性",
        r"三项不同的属性",
        r"三项属性",
        r"选择.*属性",
        r"自行选择.*属性",
    ]

    for pattern in choice_patterns:

        if re.search(pattern, text):
            return "任意"

    result = []

    for ability in ability_list:

        if ability in text:
            if ability not in result:
                result.append(ability)

    if result:
        return "、".join(result)

    return "无"


# ============================================================
# 专长
# ============================================================

def get_feat(text):
    text = clean_text(text)

    if not text:
        return "无"

    # 如果最后一个括号内容以“见”开头，则删除这个最后的括号
    match = re.search(r"[（(]([^（）()]*)[）)]\s*$", text)
    if match:
        inside = match.group(1).strip()
        if inside.startswith("见"):
            text = text[:match.start()].rstrip()

    # 处理明确的选择型专长
    if re.search(r"选择任意一种|任选一种|选择一项|任选一项", text):
        return "任意"

    return text


# ============================================================
# 技能
# ============================================================

def get_skill(text):

    if not text:
        return "无"

    text = clean_text(text)

    # --------------------------------------------------------
    # 任意技能
    # --------------------------------------------------------

    choice_patterns = [
        r"任意",
        r"任选",
        r"选择.*技能",
        r"两项.*技能",
        r"一项.*技能",
        r"任意.*技能",
    ]

    for pattern in choice_patterns:

        if re.search(pattern, text):
            return "任意"

    # --------------------------------------------------------
    # 固定技能
    # --------------------------------------------------------

    result = []

    for skill in skill_list:

        if skill in text:
            if skill not in result:
                result.append(skill)

    if result:
        return "、".join(result)

    return "无"


# ============================================================
# 工具
# ============================================================

def get_tool(text):
    text = clean_text(text)

    if not text:
        return "无"

    # 如果最后一个括号内容以“见”开头，则删除这个最后的括号
    match = re.search(r"[（(]([^（）()]*)[）)]\s*$", text)
    if match:
        inside = match.group(1).strip()
        if inside.startswith("见"):
            text = text[:match.start()].rstrip()

    # “选择一种XXX”统一改为“任意一种XXX”
    text = re.sub(r"选择一种", "任意一种", text)

    # “选择一项XXX”统一改为“任意一项XXX”
    text = re.sub(r"选择一项", "任意一项", text)

    return text.strip()


# ============================================================
# 背景对象
# ============================================================

class Background:

    def __init__(
        self,
        h3,
        chm_path,
        source
    ):

        self.name = ""
        self.name_en = ""
        self.item_id = ""

        self.ability = "无"
        self.feat = "无"
        self.skill = "无"
        self.tool = "无"

        self.source = source
        self.chm_path = chm_path

        # ====================================================
        # 名称
        # ====================================================

        self.name, self.name_en = get_background_title(h3)

        self.item_id = get_id(
            h3,
            self.name_en
        )

        # ====================================================
        # 字段
        # ====================================================

        fields = get_background_fields(h3)

        # ====================================================
        # 属性
        # ====================================================

        self.ability = get_ability(
            fields["属性值"]
        )

        # ====================================================
        # 专长
        # ====================================================

        self.feat = get_feat(
            fields["专长"]
        )

        # ====================================================
        # 技能
        # ====================================================

        self.skill = get_skill(
            fields["技能熟练"]
        )

        # ====================================================
        # 工具
        # ====================================================

        self.tool = get_tool(
            fields["工具熟练"]
        )

    # ========================================================
    # HTML
    # ========================================================

    def to_row(self):

        # 工具筛选标签
        if self.tool == "无":
            tool_tag = "无工"
        else:
            tool_tag = "有工"

        tags = [
            self.ability,
            self.skill,
            tool_tag,
            self.source,
        ]

        name_display = self.name + self.name_en

        tags_text = " ".join(tags)

        return (
            f'<TR tags="{html_escape(tags_text)}" '
            f'item="{html_escape(name_display)}">\n'

            f'<TD>'
            f'<a href="{html_escape(self.chm_path)}'
            f'#{html_escape(self.item_id)}">'
            f'{html_escape(name_display)}'
            f'</a>'
            f'</TD>\n'

            f'<TD>{html_escape(self.ability)}</TD>\n'

            f'<TD>{html_escape(self.feat)}</TD>\n'

            f'<TD>{html_escape(self.skill)}</TD>\n'

            f'<TD>{html_escape(self.tool)}</TD>\n'

            f'<TD>{html_escape(self.source)}</TD>\n'

            f'</TR>'
        )


# ============================================================
# 数据
# ============================================================

big_background_dict = {}


# ============================================================
# 处理文件
# ============================================================

def process_file(file_path, file_name):

    print("读取:", file_path)

    with open(
        file_path,
        "r",
        encoding="gbk"
    ) as f:

        data = f.read()

    soup = BeautifulSoup(
        data,
        "html.parser"
    )

    chm_path = get_chm_path(
        file_path
    )

    source = get_source(
        file_path
    )

    print("来源:", source)

    # ========================================================
    # 找 H3
    # ========================================================

    h3_list = soup.find_all("h3")

    for h3 in h3_list:

        try:

            background = Background(
                h3,
                chm_path,
                source
            )

            big_background_dict[
                background.item_id
            ] = background

            print(
                "  背景:",
                background.name,
                background.name_en,
                "| 属性:",
                background.ability,
                "| 专长:",
                background.feat,
                "| 技能:",
                background.skill,
                "| 工具:",
                background.tool
            )

        except Exception as e:

            try:
                title = h3.get_text(
                    " ",
                    strip=True
                )
            except:
                title = "未知"

            print(
                f"解析失败: {title} "
                f"({type(e).__name__}: {e})"
            )


# ============================================================
# 主流程
# ============================================================

if __name__ == "__main__":

    print("开始扫描背景文件……")

    for f in background_file_list:

        print("\n扫描:", f)

        walk_through_files(
            process_file,
            f
        )

    print(
        "\n总计:",
        len(big_background_dict)
    )

    # ========================================================
    # 模板
    # ========================================================

    with open(
        template_path,
        "r",
        encoding="gbk"
    ) as f:

        tpl = f.read()

    # ========================================================
    # 生成
    # ========================================================

    rows = []

    for background in sorted(
        big_background_dict.values(),
        key=lambda x: x.name_en.lower()
    ):

        rows.append(
            background.to_row()
        )

    html = tpl.replace(
        "{{内容}}",
        "\n".join(rows)
    )

    # ========================================================
    # 输出
    # ========================================================

    with open(
        output_path,
        "w",
        encoding="gbk"
    ) as f:

        f.write(html)

    print(
        "\n输出完成:",
        output_path
    )