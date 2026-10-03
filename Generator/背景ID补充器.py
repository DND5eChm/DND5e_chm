import os
from 文件遍历 import walk_through_files

NEEDTOBE = 20

def checkout(file_path: str,file_name: str):
    need_rewrite = False
    if "空白页模板" in file_path or "$$unsavedpage" in file_name:
        return
    content = ""
    new_content = ""
    try:
        with open(file_path,mode="r",encoding="gbk") as _f:
            content = _f.read()
    except:
        try:
            with open(file_path,mode="r",encoding="utf-8") as _f:
                content = _f.read()
                need_rewrite = True
        except:
            with open(file_path,mode="r",encoding="gbk",errors='ignore') as _f:
                content = _f.read()
    new_content = content
    # 无编码标识
    if new_content.find("coding: gbk") == -1:
        new_content = "<!-- coding: gbk -->" + new_content
        need_rewrite = True
        print(file_path+" 缺少coding标识")
    left = content.find("<body")
    right = content.find("</body>")
    if left == -1:
        left = content.find("<BODY")
    if right == -1:
        right = content.find("</BODY>")
    if left != -1 and right != -1:
        new_left = content.find(">",left)
        length = right-new_left-1
        if length < NEEDTOBE:
            print(file_path+" 文件内容少于"+str(NEEDTOBE)+"字,仅有：")
            print(content[new_left+1:right].replace("\n",""))
    else:
        print(file_path+" 缺少body标签")
        need_rewrite = True
        if left == -1:
            if "</head>" in new_content:
                new_content = new_content.replace("</head>","</head><body>")
            elif "</HEAD>" in new_content:
                new_content = new_content.replace("</HEAD>","</HEAD><BODY>")
            else:
                print(file_path+" 同时缺少head标签（需手动修正）")
        if right == -1:
            if "</html>" in new_content:
                new_content = new_content.replace("</html>","</body></html>")
            elif "</HTML>" in new_content:
                new_content = new_content.replace("</HTML>","</BODY></HTML>")
            else:
                new_content = new_content + "</body></html>"
    if need_rewrite:
        try:
            with open(file_path,mode="w",encoding="gbk",errors='ignore') as _f:
                _f.write(new_content)
                print(file_path+" 已自动修正")
        except:
            print(file_path+" 无存储权限！")

walk_through_files(checkout)