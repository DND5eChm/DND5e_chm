import os
import codecs


def convert_to_gbk(path, file_types=['.txt']):
    """
    将指定路径下的所有文本文件（包括子文件夹和子文件夹的子文件夹下的）转换为GBK格式。
    自动判断原来的格式是什么，而本身就是GBK格式的文件不转换。
    输出被转换的文件列表，格式为文件路径-文件名-原格式-新格式。

    参数：
    path：要转换的文件夹路径。
    file_types：要转换的文件类型列表，默认为['.txt']。

    返回：
    包含被转换的文件信息的列表，每个元素都是一个包含文件路径、文件名、原格式和新格式的四元组。
    """
    converted_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if not any(file.endswith(file_type) for file_type in file_types):
                continue
            file_path = os.path.join(root, file)

            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()

                # Try decoding with GBK first
                try:
                    decoded_data = raw_data.decode('gbk')
                    file_encoding = 'gbk'
                except UnicodeDecodeError:
                    # If decoding with GBK fails, try with other encodings
                    try:
                        # Using utf-8-sig to remove BOM if present
                        decoded_data = raw_data.decode('utf-8-sig')
                        file_encoding = 'utf-8-sig'
                    except UnicodeDecodeError:
                        possible_encodings = ['utf-8', 'big5', 'utf-16']
                        for encoding in possible_encodings:
                            try:
                                decoded_data = raw_data.decode(encoding)
                                file_encoding = encoding
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all encodings fail, print error message and skip the file
                            print(f"Error: cannot decode file {file_path}")
                            continue

                # Only write if the encoding is not already GBK
                if file_encoding != 'gbk':
                    try:
                        with codecs.open(file_path, 'w', encoding='GB18030') as f:
                            f.write(decoded_data)
                        converted_files.append(
                            (root, file, file_encoding, 'GB18030'))
                    except UnicodeEncodeError:
                        print(
                            f"Error: cannot encode file {file_path} to GB18030.")
                else:
                    # Append the file as already GBK, but do not perform any write operation
                    converted_files.append((root, file, 'gbk', 'gbk'))

            except Exception as err:
                print(f"Error processing file {file_path}: {str(err)}")

    # Print the list of converted files
    for file_info in converted_files:
        print(f"{file_info[0]}-{file_info[1]}-{file_info[2]}-{file_info[3]}")

    return converted_files


if __name__ == '__main__':
    folder_path = input('请输入要转换的文件夹路径：')
    file_types = input('请输入要转换的文件类型（用空格分隔多个类型，如 .txt .csv）：').split()
    converted_files = convert_to_gbk(folder_path, file_types)
    print('转换完成，以下文件已被转换为GB18030格式：')
    for file_info in converted_files:
        print(f"{file_info[0]}-{file_info[1]}-{file_info[2]}-{file_info[3]}")
