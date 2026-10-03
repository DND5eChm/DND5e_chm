import os
import re
from bs4 import BeautifulSoup
from 文件遍历 import walk_through_files


# ============================================================
# 文件路径
# ============================================================

background_file_list = [
    "玩家手册2024/角色起源/背景",
    "被遗忘的国度/费伦英雄/第一章/背景",
]

template_path = "../空白页模板/背景大速查模板.htm"
output_path = "../速查/背景大速查表.htm"


# ============================================================
# 来源
# ============================================================

source_tag = {
    "玩家手册2024": "PHB24",
    "被遗忘的国度": "FR",
}


# ============================================================
# 基础函数
# ============================================================

def clean_text(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def html_escape(text):
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def get_source(file_path):
    file_path = file_path.replace("\\", "/")

    for path_name, tag in source_tag.items():
        if path_name in file_path:
            return tag

    return ""


def get_relative_path(file_path):
    """
    速查表位于 ../速查/
    原文件位于：
        玩家手册2024/...
        被遗忘的国度/...
    """

    output_dir = os.path.dirname(os.path.abspath(output_path))
    source_file = os.path.abspath(file_path)

    relative_path = os.path.relpath(
        source_file,
        output_dir
    )

    return relative_path.replace("\\", "/")


# ============================================================
# H3
# ============================================================

def get_background_name(soup):
    h3 = soup.find("h3")

    if h3 is None:
        return "", "", ""

    full_name = clean_text(
        h3.get_text(" ", strip=True)
    )

    # 中文 + 英文
    # 例如：
    # 侍僧 Acolyte
    match = re.search(
        r"([A-Za-z][A-Za-z0-9 &'’'_-]*)$",
        full_name
    )

    if not match:
        return full_name, "", ""

    english_name = match.group(1).strip()
    chinese_name = full_name[:match.start()].strip()

    return (
        full_name,
        chinese_name,
        english_name
    )


def get_id(soup, english_name):
    h3 = soup.find("h3")

    if h3 is not None:
        old_id = h3.get("id")

        if old_id:
            return old_id

    background_id = english_name

    background_id = background_id.replace(" ", "_")
    background_id = background_id.replace("'", "")
    background_id = background_id.replace("’", "")

    background_id = re.sub(
        r"[^A-Za-z0-9_-]",
        "",
        background_id
    )

    return background_id


# ============================================================
# 字段提取
# ============================================================

def get_background_p(soup):
    """
    找到包含：
    属性值 / 专长 / 技能熟练 / 工具熟练 / 装备
    的 P。
    """

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)

        if (
            "属性值" in text
            or "专长" in text
            or "技能熟练" in text
            or "工具熟练" in text
            or "装备" in text
        ):
            return p

    return None


def get_fields(p):
    fields = {
        "属性值": "",
        "专长": "",
        "技能熟练": "",
        "工具熟练": "",
        "装备": "",
    }

    if p is None:
        return fields

    html = str(p)

    # BR 作为字段分隔
    html = re.sub(
        r"<br\s*/?>",
        "\n",
        html,
        flags=re.I
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = soup.get_text("\n")

    text = text.replace("\r", "")

    lines = []

    for line in text.split("\n"):
        line = clean_text(line)

        if line:
            lines.append(line)

    text = "\n".join(lines)

    labels = [
        "属性值",
        "专长",
        "技能熟练",
        "工具熟练",
        "装备",
    ]

    pattern = (
        "("
        + "|".join(
            re.escape(label)
            for label in labels
        )
        + ")："
    )

    matches = list(
        re.finditer(
            pattern,
            text
        )
    )

    for i, match in enumerate(matches):

        label = match.group(1)

        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        value = text[start:end].strip()

        fields[label] = value

    return fields


# ============================================================
# 属性
# ============================================================

ability_list = [
    "力量",
    "敏捷",
    "体质",
    "感知",
    "智力",
    "魅力",
]


def get_ability(text):

    if not text:
        return "无"

    # 存在选择
    if re.search(
        r"选择[A-Z]|任选|任意|或将|或提升|或提高|"
        r"\([A-Z]\)|（[A-Z]）",
        text,
        flags=re.I
    ):
        return "任意"

    result = []

    for ability in ability_list:
        if ability in text:
            result.append(ability)

    if not result:
        return "无"

    return "、".join(result)


# ============================================================
# 专长
# ============================================================

def get_feat(text):

    if not text:
        return "无"

    # 存在选项
    if re.search(
        r"选择[A-Z]|任选|任意|"
        r"\([A-Z]\)|（[A-Z]）|"
        r"或将|或者|或是",
        text,
        flags=re.I
    ):
        return "任意"

    return clean_text(text)


# ============================================================
# 技能
# ============================================================

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


def get_skill(text):

    if not text:
        return ["无"]

    if re.search(
        r"任意|任选|选择[A-Z]|"
        r"\([A-Z]\)|（[A-Z]）",
        text,
        flags=re.I
    ):
        return ["任意"]

    result = []

    for skill in skill_list:
        if skill in text:
            result.append(skill)

    if not result:
        return ["无"]

    return result


# ============================================================
# 工具
# ============================================================

def get_tool(text):

    if not text:
        return "无工"

    return clean_text(text)


# ============================================================
# 装备
# ============================================================

def get_equipment(text):

    if not text:
        return ""

    # 例如：
    # 选择A或B：（A）……8GP；或（B）50GP。
    #
    # 找出所有纯金币选项

    parts = re.split(
        r"或|或者",
        text
    )

    for part in reversed(parts):

        part = clean_text(part)

        # 去掉 A/B 标记
        part = re.sub(
            r"^[（(]?[A-Z][）)]\s*",
            "",
            part
        )

        # 纯 GP
        match = re.fullmatch(
            r"(\d+(?:\.\d+)?)\s*GP[。.]?",
            part,
            flags=re.I
        )

        if match:
            return match.group(1) + "GP"

    # 如果格式不完全标准，
    # 直接取最后一个 GP 数值
    matches = re.findall(
        r"\d+(?:\.\d+)?\s*GP",
        text,
        flags=re.I
    )

    if matches:
        return matches[-1]

    return ""


# ============================================================
# 背景对象
# ============================================================

class Background:

    def __init__(self, file_path):

        self.file_path = file_path

        self.full_name = ""
        self.chinese_name = ""
        self.english_name = ""
        self.id = ""

        self.ability = ""
        self.feat = ""
        self.skill = []
        self.tool = ""
        self.equipment = ""

        self.source = ""

        self.parse()

    def parse(self):

        with open(
            self.file_path,
            mode="r",
            encoding="gbk"
        ) as f:
            html = f.read()

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        (
            self.full_name,
            self.chinese_name,
            self.english_name
        ) = get_background_name(soup)

        if not self.full_name:
            return

        if not self.english_name:
            return

        self.id = get_id(
            soup,
            self.english_name
        )

        p = get_background_p(soup)

        fields = get_fields(p)

        self.ability = get_ability(
            fields["属性值"]
        )

        self.feat = get_feat(
            fields["专长"]
        )

        self.skill = get_skill(
            fields["技能熟练"]
        )

        self.tool = get_tool(
            fields["工具熟练"]
        )

        self.equipment = get_equipment(
            fields["装备"]
        )

        self.source = get_source(
            self.file_path
        )

    def get_tags(self):

        tags = []

        # 属性
        if self.ability:
            for value in self.ability.split("、"):
                tags.append(value)

        # 技能
        for value in self.skill:
            tags.append(value)

        # 工具
        tags.append(self.tool)

        # 来源
        if self.source:
            tags.append(self.source)

        # 去重
        result = []

        for tag in tags:
            if tag and tag not in result:
                result.append(tag)

        return " ".join(result)

    def to_row(self):

        relative_path = get_relative_path(
            self.file_path
        )

        href = (
            relative_path
            + "#"
            + self.id
        )

        name = (
            html_escape(self.chinese_name)
            + html_escape(self.english_name)
        )

        link = (
            '<a href="'
            + href
            + '">'
            + name
            + "</a>"
        )

        skill_text = "、".join(
            self.skill
        )

        tags = self.get_tags()

        return (
            '<TR tags="'
            + html_escape(tags)
            + '" item="'
            + html_escape(self.full_name)
            + '">'

            "<TD>"
            + link
            + "</TD>"

            '<TD width=280>'
            + html_escape(self.ability)
            + "</TD>"

            "<TD>"
            + html_escape(self.feat)
            + "</TD>"

            '<TD width=160>'
            + html_escape(skill_text)
            + "</TD>"

            '<TD width=160>'
            + html_escape(self.tool)
            + "</TD>"

            '<TD width=80>'
            + html_escape(self.equipment)
            + "</TD>"

            '<TD width=120>'
            + html_escape(self.source)
            + "</TD>"

            "</TR>\n"
        )


# ============================================================
# 扫描
# ============================================================

background_list = []


def process_file(file_path: str, file_name: str):

    try:

        background = Background(
            file_path
        )

        if not background.full_name:
            print(
                "【跳过】无法识别："
                + file_path
            )
            return

        if not background.english_name:
            print(
                "【跳过】无法识别英文名："
                + file_path
            )
            return

        background_list.append(
            background
        )

    except Exception as e:

        print(
            "\n【处理失败】"
            + file_path
        )

        print(
            "  "
            + str(e)
        )


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":

    print("开始扫描背景文件……")

    for background_path in background_file_list:

        if not os.path.exists(
            background_path
        ):
            print(
                "【路径不存在】"
                + background_path
            )
            continue

        print(
            "\n开始扫描："
            + background_path
        )

        walk_through_files(
            process_file,
            background_path
        )

    print(
        "\n共读取背景："
        + str(len(background_list))
    )

    # 按英文名排序
    background_list.sort(
        key=lambda x:
            x.english_name.lower()
    )

    # ========================================================
    # 读取模板
    # ========================================================

    with open(
        template_path,
        mode="r",
        encoding="gbk"
    ) as f:
        template = f.read()

    # ========================================================
    # 生成内容
    # ========================================================

    content = ""

    for background in background_list:
        content += background.to_row()

    # ========================================================
    # 替换模板
    # ========================================================

    output = template.replace(
        "{{内容}}",
        content
    )

    # ========================================================
    # 写出
    # ========================================================

    output_dir = os.path.dirname(
        output_path
    )

    if (
        output_dir
        and not os.path.exists(output_dir)
    ):
        os.makedirs(output_dir)

    with open(
        output_path,
        mode="w",
        encoding="gbk"
    ) as f:
        f.write(output)

    print(
        "\n生成完成："
    )

    print(
        output_path
    )