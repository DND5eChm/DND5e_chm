import os
from 文件遍历 import walk_through_files

rename_list: list = []

def record_rename_as(file_path,file_name):


if __name__ == "__main__":
    print("处理开始")
    walk_through_files(record_rename_as,"玩家手册2024")
    start_renaming()