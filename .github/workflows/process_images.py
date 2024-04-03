import os
import re

def process_markdown_files(directory):
    md_file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                md_file_paths.append(os.path.join(root, file))

    # 更精确的查找和替换逻辑
    url_pattern = re.compile(r'\]\(img/')
    url_replace = r']({{ site.baseurl }}/img/'

    for md_file in md_file_paths:
        with open(md_file, 'r+', encoding='utf-8') as file:
            content = file.read()
            updated_content = re.sub(url_pattern, url_replace, content)
            if updated_content != content:
                file.seek(0)
                file.write(updated_content)
                file.truncate()

if __name__ == "__main__":
    process_markdown_files('_posts')
