import os

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
            if data not in result:
                result.append(data)
    result.sort()
    print("、".join(result).replace("\n",""))
    with open(file,'w',encoding='utf-8') as _f:
        _f.writelines(result)
    return result

if __name__ == "__main__":
    thanks_list_1 = load_and_update(THANKS_PATH_1)
    thanks_list_2 = load_and_update(THANKS_PATH_2)
    thanks_list_3 = load_and_update(THANKS_PATH_3)
    output = ""
    with open(TEMPLATE_PATH,'r',encoding='gbk') as _f:
        output = _f.read()
    output = output.replace("{1}","、".join(thanks_list_1).replace("\n","")).replace("{2}","、".join(thanks_list_2).replace("\n","")).replace("{3}","、".join(thanks_list_3).replace("\n",""))
    with open(TEMPLATE_PATH,'w',encoding='gbk') as _f:
         _f.write(output)
     print("更新完毕！")