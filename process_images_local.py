import os
import re
import sys

def process_file(file_path, operation):
    url_pattern_add = re.compile(r'\]\(\.\/img/')
    url_pattern_remove = re.compile(r'\]\({{ site.baseurl }}/img/')
    url_replace_add = r']({{ site.baseurl }}/img/'
    url_replace_remove = r'](./img/'

    with open(file_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        if operation == "+":
            updated_content = re.sub(url_pattern_add, url_replace_add, content)
        elif operation == "-":
            updated_content = re.sub(url_pattern_remove, url_replace_remove, content)
        else:
            print("无效的操作类型")
            return

        if updated_content != content:
            file.seek(0)
            file.write(updated_content)
            file.truncate()

def process_directory(directory, operation):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                process_file(os.path.join(root, file), operation)

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("使用方法: python process_images.py <文件/目录路径> <+/-> [指定文件名]")
        print("         +： add imgurl;  -： remove imgurl")
        print("Usage:   python process_images.py test.md +")
    else:
        path = sys.argv[1]
        operation = sys.argv[2]
        if len(sys.argv) == 4:
            # 如果提供了第三个参数（指定文件名），只处理该文件
            specific_file = sys.argv[3]
            specific_file_path = os.path.join(path, specific_file)
            if os.path.exists(specific_file_path) and specific_file_path.endswith(".md"):
                process_file(specific_file_path, operation)
                print("处理完成:", specific_file_path)
            else:
                print("指定的文件不存在或不是Markdown文件")
        else:
            # 处理整个目录或单个文件
            if os.path.isdir(path):
                process_directory(path, operation)
            elif os.path.isfile(path) and path.endswith(".md"):
                process_file(path, operation)
                print("处理完成:", path)
            else:
                print("路径不是Markdown文件或目录")
