import os
from 文件遍历 import walk_through_files

rename_list: list = []

def record_rename_as(file_path,file_name):
    data = ""
    with open(file_path,mode="r",encoding="gbk") as _f:
        data = _f.read()
    title = data[data.find("<title>")+7:data.find("</title>")].strip()
    if "/" in title:
        title = title.replace("/","_")
    if "\n" in title:
        title = title.replace("\n","_")
    #print(file_name+" → "+title)
    rename_list.append([file_path,title])

def start_renaming():
    for record in rename_list:
        dirname = os.path.dirname(record[0])
        new_path = dirname+"\\"+record[1]+".htm"
        os.rename(record[0],new_path)
        print(record[0]+" 已重命名为: "+new_path)

if __name__ == "__main__":
    print("处理开始")
    walk_through_files(record_rename_as,"玩家手册2024（试读版）")
    start_renaming()