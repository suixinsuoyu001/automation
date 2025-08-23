import os
from func.common import log
import cloudscraper
from bs4 import BeautifulSoup

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

scraper = cloudscraper.create_scraper()  # 全局 scraper


def get_jpg_url(url):
    try:
        resp = scraper.get(url, proxies=proxies, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        img_tag = soup.select_one('#image-container img')
        if img_tag:
            img_url = img_tag.get('data-src') or img_tag.get('src')
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
        log(f"[WARN] 未找到图片标签: {url}")
        return None
    except Exception as e:
        log(f"[ERROR] 请求或解析出错: {url} -> {e}")
        return None


def get_jpg(url, save_path, name):
    try:
        ext = os.path.splitext(url)[-1]  # 获取扩展名
        n = url.split('/')[-1].split('.')[0]  # 图片编号
        save_dir = os.path.join(save_path, name)
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{n}{ext}")
        file_path = file_path.replace('webp','jpg')
        resp = scraper.get(url, stream=True, proxies=proxies, timeout=10)
        if resp.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            log(f"[INFO] 下载成功: {file_path}")
        else:
            log(f"[ERROR] 请求失败: {url} -> {resp.status_code}")
    except Exception as e:
        log(f"[ERROR] 下载出错: {url} -> {e}")


def get_jpgs(id, Artists, name, n=1):
    while True:
        url = f'https://nhentai.net/g/{id}/{n}/'
        jpg_url = get_jpg_url(url)
        if not jpg_url:
            break
        get_jpg(jpg_url, f"E:/images/{Artists}/", name)
        n += 1
    log(f"[INFO] {name} 完成")


if __name__ == '__main__':
    get_jpgs('557940', '戦乙女-mashu', '女武神')
