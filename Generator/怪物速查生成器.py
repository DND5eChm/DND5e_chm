import os
import chardet
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
type_list = ["异怪", "野兽", "天族", "构装", "龙类", "元素", "妖精", "邪魔", "巨人", "类人", "怪兽", "泥怪", "植物", "亡灵", "天族或邪魔"]
cr_list = ["0", "1/8", "1/4", "1/2"] + [str(i) for i in range(1, 31)]  

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
        self.monster_legendary = "无"  # 新增传奇动作属性

        self.monster_source_tag = source_tag
        self.monster_source_priority = source_priority[source_tag]
        
        self.chm_path = chm_path
        self.legacy = False
        
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(content, "html.parser")
            
            # 从H5标签读取怪物名称和ID
            h5_tag = soup.find('h5')
            if h5_tag:
                self.monster_name = h5_tag.get_text().strip()
                self.monster_id = h5_tag.get('id', '').strip()
                if not self.monster_id:
                    self.monster_id = f"unknown_{hash(content) % 10000}"
            else:
                self.monster_name = "未知怪物"
                self.monster_id = f"unknown_{hash(content) % 10000}"
            
            # 查找子行信息(紧跟在H5后的div或其他元素)
            subline_element = None
            if h5_tag:
                # 查找包含类型信息的div
                next_sibling = h5_tag.find_next_sibling()
                while next_sibling:
                    if next_sibling.name == 'div' and 'sub-line' in next_sibling.get('class', []):
                        subline_element = next_sibling
                        break
                    elif next_sibling.name == 'div' and any(size in next_sibling.get_text() for size in size_list):
                        subline_element = next_sibling
                        break
                    next_sibling = next_sibling.find_next_sibling()
            
            if subline_element:
                self.monster_subline = subline_element.get_text().strip()
            else:
                # 备用方法：查找所有文本行中包含体型信息的行
                all_text = soup.get_text()
                lines = [line.strip() for line in all_text.splitlines() if line.strip()]
                for line in lines[1:4]:  # 检查前几行
                    if any(size in line for size in size_list):
                        self.monster_subline = line
                        break
                if not self.monster_subline and len(lines) > 1:
                    self.monster_subline = lines[1]
            
            # 解析体型
            for size in size_list:
                if size in self.monster_subline:
                    self.monster_size = size
                    break
            
            # 解析类型
            for monster_type in type_list:
                if monster_type in self.monster_subline:
                    self.monster_type = monster_type
                    break
            
            # 解析标签
            if "（" in self.monster_subline and "）" in self.monster_subline:
                left = self.monster_subline.find("（") + 1
                right = self.monster_subline.find("）", left)
                if right > left:
                    self.monster_tag = self.monster_subline[left:right].strip()
        
            # 改进的CR解析
            self._parse_cr_improved(soup, content)
            
            # 检测传奇动作
            self._parse_legendary_actions(soup, content)
                
        except Exception as e:
            print(f"初始化怪物时出错: {str(e)}")
            # 设置默认值
            self.monster_name = "未知怪物"
            self.monster_id = f"unknown_{hash(content) % 10000}"
            self.monster_subline = "未知类型"
            self.monster_size = "中型"
            self.monster_type = "怪兽"
            self.monster_tag = ""
            self.monster_cr = "0"
            self.monster_legendary = "无"

    def _parse_cr_improved(self, soup, content):
        """改进的CR解析方法"""
        self.monster_cr = "0"  # 默认值
        
        # 方法1: 查找包含CR的强调标签
        cr_tags = soup.find_all(['strong', 'b'], string=lambda text: text and ('CR' in text or '挑战等级' in text))
        for tag in cr_tags:
            parent = tag.parent
            if parent:
                parent_text = parent.get_text()
                self._extract_cr_from_text(parent_text)
                if self.monster_cr != "0":
                    return
        
        # 方法2: 查找包含CR的表格单元格
        td_tags = soup.find_all('td')
        for td in td_tags:
            td_text = td.get_text()
            if 'CR' in td_text or '挑战等级' in td_text:
                self._extract_cr_from_text(td_text)
                if self.monster_cr != "0":
                    return
        
        # 方法3: 在整个内容中搜索CR模式
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.splitlines() if line.strip()]
        for line in lines:
            if 'CR' in line or '挑战等级' in line:
                self._extract_cr_from_text(line)
                if self.monster_cr != "0":
                    return
    
    def _extract_cr_from_text(self, text):
        """从文本中提取CR值"""
        import re
        
        # 匹配各种CR格式的正则表达式
        cr_patterns = [
            r'CR\s*(?:</(?:strong|b)>)?\s*(\d+(?:/\d+)?)',  # CR 1, CR</strong> 1/2
            r'挑战等级\s*(?:</(?:strong|b)>)?\s*(\d+(?:/\d+)?)',  # 挑战等级 1
            r'CR\s*(?:</(?:strong|b)>)?\s*：\s*(\d+(?:/\d+)?)',  # CR：1
            r'挑战等级\s*(?:</(?:strong|b)>)?\s*：\s*(\d+(?:/\d+)?)',  # 挑战等级：1
        ]
        
        for pattern in cr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cr_value = match.group(1)
                if cr_value in cr_list:
                    self.monster_cr = cr_value
                    return True
        
        return False

    def _parse_legendary_actions(self, soup, content):
        """检测是否有传奇动作"""
        self.monster_legendary = "无"  # 默认值
        
        # 方法1: 查找h6标签中包含"传奇动作"的内容
        h6_tags = soup.find_all('h6')
        for h6 in h6_tags:
            h6_text = h6.get_text()
            if '传奇动作' in h6_text and 'Legendary Actions' in h6_text:
                self.monster_legendary = "有"
                return
        
        # 方法2: 在整个内容中搜索传奇动作标识
        all_text = soup.get_text()
        if '传奇动作Legendary Actions' in all_text or '传奇动作 Legendary Actions' in all_text:
            self.monster_legendary = "有"
            return

    def output_id_and_link(self,_class="万兽大全") -> str:
        display_name = self.monster_name

        id_and_link = "<a href=\""+self.chm_path+"#"+self.monster_id+"\">"+display_name+"</a>"

        if _class == "万兽大全":
            tags = [
                self.monster_size,
                self.monster_type,
                self.monster_legendary,
                self.monster_cr,
            ]
            labels = [
                id_and_link,
                self.monster_size,
                self.monster_type,
                self.monster_legendary,
                self.monster_cr
            ]
            id_and_link = "<TR tags=\"" +" ".join(tags)+"\" monster=\""+self.monster_name+"\"><TD>"+"</TD><TD>".join(labels)+"</TD></TR>"
        elif self.monster_source_tag not in ["","MM25"]: #角标
            id_and_link += "<sup>"+self.monster_source_tag+"</sup>"
        return id_and_link
    
    def output_database(self) -> list[str]:
        output = [self.monster_name,self.monster_source_tag,"怪物",self.monster_subline]
        return output

big_monster_list: dict[str, Monster] = {}
big_monster_list_keys: list[str] = []

def process_file(file_path: str, file_name: str):
    try:
        # 检测文件编码
        with open(file_path, mode="rb") as _f:
            raw_data = _f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'gbk'
        
        # 使用检测到的编码读取文件
        with open(file_path, mode="r", encoding=encoding, errors='ignore') as _f:
            data = _f.read()
        
        # 检查文件内容格式
        body_start = data.find("<body>")
        body_end = data.find("</body>")
        
        if body_start == -1 or body_end == -1:
            print(f"警告: {file_path} 不是有效的HTML文件，跳过处理")
            return
            
        data = data[body_start+6:body_end]
        
        # 改进内容分割逻辑，确保每个H5标签开始一个新条目
        soup = BeautifulSoup(data, "html.parser")
        h5_tags = soup.find_all('h5')
        
        contents = []
        for i, h5_tag in enumerate(h5_tags):
            # 获取从当前H5到下一个H5之间的所有内容
            content_elements = []
            current = h5_tag
            
            while current:
                content_elements.append(str(current))
                current = current.next_sibling
                
                # 如果遇到下一个H5标签，停止
                if current and current.name == 'h5':
                    break
            
            if content_elements:
                content = ''.join(content_elements)
                if content.strip():  # 只添加非空内容
                    contents.append(content)
        
        # 修复路径处理
        chm_path = file_path.replace("\\", "/")
        if "DND5e_chm/" in chm_path:
            chm_path = chm_path.split("DND5e_chm/")[1]
        else:
            chm_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
        
        book = chm_path.split("/")[0] if "/" in chm_path else file_name
        source = source_tag.get(book, book)
        
        print(f"开始处理 {book} 内的资源，共找到 {len(contents)} 个条目。")
        
        # 获取资源
        success_count = 0
        for i, content in enumerate(contents):
            try:
                # 获取怪物
                monster = Monster(content, chm_path, source)
                
                # 验证怪物数据的完整性
                if not monster.monster_name or monster.monster_name == "未知怪物":
                    print(f"跳过无效条目 {i+1}: 无法获取怪物名称")
                    continue
                
                if monster.monster_id in big_monster_list.keys():
                    big_monster_list[monster.monster_id].legacy = True
                    big_monster_list["zzzzzzzzz" + monster.monster_id] = big_monster_list[monster.monster_id]
                    big_monster_list_keys.append("zzzzzzzzz" + monster.monster_id)
                
                big_monster_list[monster.monster_id] = monster
                if monster.monster_id not in big_monster_list_keys:
                    big_monster_list_keys.append(monster.monster_id)
                    success_count += 1
                    print(f"成功添加怪物: {monster.monster_name} (CR: {monster.monster_cr}, 传奇动作: {monster.monster_legendary})")

            except Exception as e:
                print(f"解析第 {i+1} 个条目时出错: {str(e)}")
                continue
        
        print(f"成功处理 {success_count} 个怪物")
        
    except Exception as e:
        print(f"处理文件 {file_path} 时发生错误: {str(e)}")

if __name__ == "__main__":
    try:
        # 检查必要的文件和目录
        template_path = os.path.abspath(html_template_big)
        if not os.path.exists(template_path):
            print(f"错误: 找不到模板文件 {template_path}，请检查路径")
            exit(1)

        target_folder = "./Generated"
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        # 遍历怪物文件
        for file in monster_file_list:
            print(f"开始处理文件: {file}")
            walk_through_files(process_file, file)

        # 生成速查
        try:
            # 尝试多种编码读取模板文件
            template_big = None
            for encoding in ['gbk', 'gb2312', 'utf-8']:
                try:
                    with open(template_path, mode="r", encoding=encoding, errors='ignore') as _f:
                        template_big = _f.read()
                    print(f"成功使用 {encoding} 编码读取模板文件")
                    break
                except:
                    continue
            
            if template_big is None:
                raise Exception("无法读取模板文件")

        except Exception as e:
            print(f"读取模板文件时出错: {str(e)}")
            exit(1)

        # 生成速查大表
        big_monster_list_keys.sort()
        print(f"已发现合计 {len(big_monster_list_keys)} 个怪物。")
        
        # 确保输出目录存在
        output_dir = "../速查"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_file = os.path.join(output_dir, "5E万兽大全.html")
        
        # 生成内容
        monster_rows = []
        for monster_id in big_monster_list_keys:
            try:
                row = big_monster_list[monster_id].output_id_and_link(_class="万兽大全")
                monster_rows.append(row)
            except Exception as e:
                print(f"生成怪物 {monster_id} 的行时出错: {str(e)}")
        
        # 修复模板替换逻辑 - 使用正确的占位符
        final_content = template_big.replace("怪物列表内容", "\n".join(monster_rows))
        
        # 如果第一个替换没有成功，尝试其他可能的占位符
        if "怪物列表内容" not in template_big:
            # 尝试其他可能的占位符格式
            possible_placeholders = [
                "     内容     ",
                "{{内容}}",
                "内容占位符",
                "MONSTER_LIST_CONTENT"
            ]
            for placeholder in possible_placeholders:
                if placeholder in template_big:
                    final_content = template_big.replace(placeholder, "\n".join(monster_rows))
                    break
                    
        # 清理重复的HTML结构
        final_content = final_content.replace("</table>\n</body>\n</html>\n</table>\n</body>\n</html>", "</table>\n</body>\n</html>")
        
        with open(output_file, mode="w", encoding="gbk", errors='ignore') as _f:
            _f.write(final_content)
            
        print(f"成功生成速查文件: {output_file}")
        print(f"占位符替换状态: {'成功' if '怪物列表内容' not in final_content else '失败'}")
        
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
