import os
import math
from pypinyin import lazy_pinyin

TEMPLATE_PATH = "../空白页模板/鸣谢列表模板.htm"
THANKS_PATH_1 = "../鸣谢/翻译贡献者列表.txt"
THANKS_PATH_2 = "../鸣谢/CHM制作者列表.txt"
THANKS_PATH_3 = "../鸣谢/纠错参与者列表.txt"
OUTPUT_PATH = "../鸣谢列表.htm"

def load_and_update(file: str) -> list:
    if os.path.exists(file):
        print("已发现 " + os.path.basename(file)+" ：")
    result = []
    with open(file,'r',encoding='utf-8') as _f:
        datas = _f.readlines()
        for data in datas:
            data = data.strip()
            if data not in result and len(data) > 0:
                result.append(data)
    # 排序
    #result.sort()
    # 用拼音排序
    result.sort(key=lambda name: " ".join(lazy_pinyin(name.upper())))
    print("、".join(result))
    with open(file,'w',encoding='utf-8') as _f:
        _f.writelines([line+"\n" for line in result])
    return result

def generate_output(data_list: list) -> str:
    # CHM不支持多列布局css，只能手动打个表了
    if len(data_list) < 4:
        return "<table><tr>"+"".join(["<td>"+data+"</td>" for data in data_list])+"</tr></table>"
    quarter = math.ceil(len(data_list)/4)
    split_list = [data_list[:quarter],data_list[quarter:quarter*2],data_list[quarter*2:quarter*3],data_list[quarter*3:]]
    len_list = [len(split_list[0]),len(split_list[1]),len(split_list[2]),len(split_list[3])]
    result =[]
    for index in  range(quarter):
        sub_result = []
        for sub_index in range(4):
            if index < len_list[sub_index]:
                sub_result.append("<td>"+split_list[sub_index][index]+"</td>")
        result.append("<tr>" + "".join(sub_result) + "</tr>\n")
    return "<table>\n"+"\n".join(result)+"\n</table>"
    
    "<br>".join(thanks_list_1)
if __name__ == "__main__":
    thanks_list_1 = load_and_update(THANKS_PATH_1)
    print("已更新翻译贡献者列表。")
    thanks_list_2 = load_and_update(THANKS_PATH_2)
    print("已更新CHM制作者列表。")
    thanks_list_3 = load_and_update(THANKS_PATH_3)
    print("已更新纠错参与者列表。")
    output = ""
    with open(TEMPLATE_PATH,'r',encoding='gbk') as _f:
        output = _f.read()
    output = output.replace("{1}",generate_output(thanks_list_1)).replace("{2}",generate_output(thanks_list_2)).replace("{3}",generate_output(thanks_list_3))
    with open(OUTPUT_PATH,'w',encoding='gbk',errors='ignore') as _f:
         _f.write(output)
    print("更新完毕！")
