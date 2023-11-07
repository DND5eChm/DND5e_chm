import os
import string
import codecs
import chardet

def convert(file, in_enc="GBK", out_enc="UTF-8"):
    in_enc = in_enc.upper()
    out_enc = out_enc.upper()
    try:
        print("convert [ " + file.split('\\')[-1] + " ].....From " + in_enc + " --> " + out_enc )
        f = codecs.open(file, 'r', in_enc,errors='ignore')
        new_content = f.read()
        codecs.open(file, 'w', out_enc).write(new_content)
    # print (f.read())
    except IOError as err:
        print("I/O error: {0}".format(err))

with open("D:\GitHub\DND5e_chm\要处理的gb2312.txt", "r", encoding='utf-8') as _f:
    _data = _f.readlines()
    for filePath in _data:
        #print(line.strip())
        with open(filePath.strip(), "rb") as f:
            data = f.read()
            codeType = chardet.detect(data)['encoding']
            convert(filePath.strip(), codeType, 'UTF-8')