import re
from collections import Counter
from 文件遍历 import walk_through_files

fileCss = ""
fontName = ""
fontSize = ""

def checkClass(match):
    return str(match.group(0)) if '.'+str(match.group(1)) in fileCss else str(match.group(2))

def replaceFont(match):
    style = str(match.group(2))
    if not style[-1] == ';':
        style = style +';'
    if fontName != "":
        if ("FONT-FAMILY:" in style) or ("font-family:" in style):
            style = re.sub(r'((?:FONT-FAMILY|font-family):\s)(.*?)(;)', r'\1'+fontName+r'\3', style)
        else:
            style = style + ' font-family: '+fontName+';'
    if fontSize != "":
        if ("FONT-SIZE:" in style) or ("font-size:" in style):
            style = re.sub(r'((?:FONT-SIZE|font-size):\s)(.*?)(pt;)', r'\1'+fontSize+r'\3', style)
        else:
            style = style + ' font-family: '+fontSize+'pt;'

    return str(match.group(1))+style+str(match.group(3))

def cleanNull(source):
    source = re.sub(r'<(SPAN|span)\s*style="">((.|\n)*?)</\1>', r'\2', source)
    source = re.sub(r'\s+style=""', '', source)
    source = re.sub(r'<([BbIi])></\1>', '', source)
    source = re.sub(r'</([BbIi])><\1>', '', source)
    # 这个坏格式
    # source = re.sub(r'<(SPAN|span)[^>]*?>(<BR>)</\1>', r'\2', source)
    return source

def cleanMS(source):
    source = re.sub(r'(\s)?mso-.*?"', '"', source)
    source = re.sub(r'(\s)?mso-.*?;', '', source)   
    source = re.sub(r'xmlns:[vowm]=".*?"\n?', '', source)
    source = re.sub(r'<(SPAN|span)(\s)+?style="[^>]*?"><o:p></o:p></\1>', '', source)
    
    return source

def cleanFont(source):
    global fontName, fontSize, fileCss

    source = re.sub(r'(<(SPAN|span)(?:\s)+?style=".*?FONT-FAMILY:\s(.*?);[^>]*?">)<FONT\sface=\3>((?:\n|.)*?)</FONT></\2>', r'\1\4</\2>', source)

    if re.match(r'<link\srel="stylesheet"\stype="text/css"\shref', source) is None:
        cssMatch = re.search(r'<style>[^<]*?</style>', source)
        fileCss = '' if cssMatch is None else cssMatch.group(0)
        source = re.sub(r'\sclass=([^\s>]*?)([\s>])', checkClass, source)

    fontName = Counter([str(i.group(1)) for i in re.finditer('(?:FONT-FAMILY|font-family):\s(.*?)[;"]',source)]).most_common(1)[0][0]
    fontSize = Counter([str(i.group(1)) for i in re.finditer('(?:FONT-SIZE|font-size):\s(\d*?)pt',source)]).most_common(1)[0][0]
    
    source = re.sub(r'\s?(?:FONT-FAMILY|font-family):\s'+fontName+';?', '', source)
    source = re.sub(r'\s?(?:FONT-SIZE|font-size):\s'+fontSize+'pt;?', '', source)

    #这个还是得考虑把body style 提到<style>里才行
    source = re.sub(r'(<body(?:.|\n)*?style=")((?:.|\s)*?)("[^>]*?>)', replaceFont, source)

    # 没搞明白为什么不生效
    source = re.sub(r'<B>(<(SPAN|span)(?:\s)*?style=".*?FONT-WEIGHT:\sbold;[^>]*?">)((?:\n|.)*?)</\2></B>', r'\1\3</\2>', source)
    source = re.sub(r'<I>(<(SPAN|span)(?:\s)*?style=".*?FONT-STYLE:\sitalic;[^>]*?">)((?:\n|.)*?)</\2></I>', r'\1\3</\2>', source)
    # source = re.sub(r'</([BbIi])><\1>', '', source)

    return source

def cleanFile(filename, encoding="gbk", outputname=""):
    if outputname == "":
        outputname = filename
    source = ""
    with open(filename, mode="r", encoding=encoding) as _f:
        source = _f.read()
    source = cleanMS(source)
    source = cleanNull(source)
    source = cleanFont(source)
    source = cleanNull(source)

    with open(outputname, mode="w", encoding=encoding) as _f:
        _f.write(source)

def clean(file_path: str,file_name: str):
    if "$$" not in file_name and "空白页模板" not in file_path:
        cleanFile(file_path, "gbk", file_path)

if __name__ == "__main__":
    walk_through_files(clean)
    #cleanFile("伤害与治疗.htm", outputname="output1.htm")