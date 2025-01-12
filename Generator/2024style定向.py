import os
from 文件遍历 import get_base_path,walk_through_files

base_path = get_base_path()

def fix_style_link(file_path,file_name):
    data = ""
    with open(file_path,mode="r",encoding="gbk") as _f:
        data = _f.read()
    if "<link rel=" in data and "style.css\">" in data:
        left = data.find("<link rel=")+29
        right = data.find("style.css\">")
        #print(data[:left]+"xxx"+data[right:])
        #获取深度
        relpath = os.path.relpath(file_path,base_path)
        depth = relpath.count("\\")
        print(relpath+"："+str(depth))
        middle_text = "./"
        if depth == 2:
            middle_text = "../"
        elif depth == 3:
            middle_text = "../../"
        data = data[:left]+middle_text+data[right:]
        with open(file_path,mode="w",encoding="gbk") as _f:
            _f.write(data)
    #<link rel="stylesheet" href="../style.css">

if __name__ == "__main__":
    walk_through_files(fix_style_link,"玩家手册2024")