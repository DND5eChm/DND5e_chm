import os
from 文件遍历 import walk_through_files

def test(file_path,file_name):
    print(file_path)

if __name__ == "__main__":
    walk_through_files(test,"印记城与外域/新法术.htm")