import os

head_left = "<html>\n<head><title>"
head_right = "</title>\n"\
"<meta name=\"GENERATOR\" content=\"WinCHM\">\n"\
"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\n"\
"<style>"\
"html,body { \n"\
"	font-family: Arial, Helvetica, sans-serif;\n"\
"}\n"\
"</style></head>"

#print(head_left + "abc" + head_right)

for filepath,dirnames,filenames in os.walk('D:\GitHub\DND5e_chm'):
    for filename in filenames:
        if filename.endswith(".htm") or filename.endswith(".html"):
            file = os.path.join(filepath,filename)
            #print(file)
            try:
                text: str = ""
                need_fix: bool = False
                with open(file, "r",encoding='UTF-8') as f:
                    text = f.read()
                    if text.find("head") == -1:
                        print(file+"缺少head")
                        need_fix = True
                if need_fix:
                    text = text.replace("<html>",head_left + filename + head_right,1)
                    with open(file, "w",encoding='UTF-8') as f:
                        f.write(text)
                        print("已处理")
            except:
                print(file+"无法识别")
