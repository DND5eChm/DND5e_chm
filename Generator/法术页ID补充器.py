import os
from 文件遍历 import walk_through_files

TARGET = "斯翠海文：混沌研习/玩家选项/法术详述.html"

def process_file(file_path: str,file_name: str):
    contents = []
    new_contents = []
    with open(file_path,mode="r",encoding="gb2312") as _f:
        contents = _f.readlines()
    for content in contents:
        if "<H4>" in content:
            left = content.find("<H4>")
            right = content.find("</H4>")
            full_name = content[left+4:right].strip()
            if "｜" in full_name:
                english_name = full_name.split("｜")[1].replace(" ","_")
                content = content.replace("<H4>","<H4 id=\""+english_name+"\">",1)
                print(english_name)
            else:
                print(file_path + "的" + full_name + "格式有误！")
        new_contents.append(content)
    
    with open(file_path,mode="w",encoding="gb2312") as _f:
        _f.writelines(new_contents)

if __name__ == "__main__":
    walk_through_files(process_file,TARGET)
     