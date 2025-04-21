import os
import chardet
import logging
def convert_encoding_to_utf8(file_path):
    """将文件从GB2312转换为UTF-8编码"""
    try:
        # 检测文件编码
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
        # 如果是GB2312编码则转换
        if result['encoding'] and 'gb2312' in result['encoding'].lower():
            content = raw_data.decode('gb2312')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已转换: {file_path}")
        else:
            print(f"无需转换: {file_path} (检测编码: {result['encoding']})")
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
def process_directory(directory):
    """递归处理目录中的所有HTML文件"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.htm') or file.endswith('.html'):
                file_path = os.path.join(root, file)
                convert_encoding_to_utf8(file_path)
# 配置日志(同时输出到文件和控制台)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 文件日志
file_handler = logging.FileHandler('encoding_conversion.log', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)
logger.addHandler(console_handler)
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"开始处理目录: {current_dir}")
    process_directory(current_dir)
    logging.info("转换完成")
    print("转换完成，详情请查看encoding_conversion.log文件")
