from tool.图片爬取.e_hentai.下载函数 import get_url_jpg

if __name__ == "__main__":

    with open('tool/图片爬取/e_hentai/ChocoPizza_AI图片链接/2.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f]

    for i,l in enumerate(lines):
        get_url_jpg(l,r'E:\images\ChocoPizza\2',f'{i+1}.jpg')