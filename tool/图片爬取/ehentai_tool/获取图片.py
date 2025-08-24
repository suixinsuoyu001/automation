from tool.图片爬取.ehentai_tool.下载函数 import get_url_jpg

if __name__ == "__main__":

    with open('tool/图片爬取/ehentai_tool/ChocoPizza_AI图片链接/1.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f]

    for i,l in enumerate(lines):
        get_url_jpg(l,r'E:\images\ChocoPizza\1',f'{i+1}.jpg')

    # get_url_jpg('https://e-hentai.org/s/2c0cce58ee/3170851-1013', r'E:\images\ChocoPizza\1', f'451.jpg')