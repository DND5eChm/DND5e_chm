import os
import re

def get_base_path():
    """
    获取工程的基本路径
    """
    folder = os.path.abspath(os.path.join(os.path.abspath(__file__),"..\\..\\"))
    return folder

def walk_through_files(process_func, folder_name: str = "", filename_re_exp: str = ".*\.htm*"):
    """
    遍历给定文件夹下的所有文件
    process_func: 为每个文件执行的方法：process_func(完整文件路径，无后缀文件名)
    folder: 项目内文件夹，默认为整个不全书项目
    filename_re_exp: 文件名的正则表达式判定，默认仅匹配.htm与.html
    """
    folder_path = get_base_path()
    if folder_name:
        folder_path = folder_path+"/"+folder_name
    if os.path.isfile(folder_path):
        filename = os.path.basename(folder_path)
        if re.search(filename_re_exp, filename):
            process_func(folder_path,os.path.splitext(filename)[0])
    else:
        for filepath,dirnames,filenames in os.walk(folder_path):
            for filename in filenames:
                if re.search(filename_re_exp, filename):
                    file_full_path = os.path.join(filepath,filename)
                    process_func(file_full_path,os.path.splitext(filename)[0])