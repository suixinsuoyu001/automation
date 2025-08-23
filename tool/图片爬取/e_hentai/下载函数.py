import os
import cloudscraper
from bs4 import BeautifulSoup
from func.common import log

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

def get_url_text(url):
    """获取网页文本"""
    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(url, proxies=proxies, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            log(f"请求失败: {resp.status_code}")
    except Exception as e:
        log(f"请求出错: {e}")
    return None


def get_image_url(page_text):
    """解析页面文本获取真实图片URL"""
    if not page_text:
        return None
    soup = BeautifulSoup(page_text, "html.parser")
    img_tag = soup.find("img", id="img")  # e-hentai 主图片id是 "img"
    if img_tag:
        img_url = img_tag.get("src")
        return img_url
    log("未找到图片标签")
    return None


def image_download(img_url, save_path, file_name=None):
    """下载图片并统一保存为 .jpg"""
    if not img_url:
        log("图片URL为空，无法下载")
        return

    if not file_name:
        # 默认用 URL 的最后一段做文件名
        file_name = os.path.basename(img_url).split('?')[0].split('.')[0] + ".jpg"

    # 创建保存文件夹
    os.makedirs(save_path, exist_ok=True)
    save_file = os.path.join(save_path, file_name)

    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(img_url, proxies=proxies, stream=True, timeout=10)
        if resp.status_code == 200:
            with open(save_file, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            log(f"图片下载成功: {save_file}")
        else:
            log(f"图片下载失败, 状态码: {resp.status_code}")
    except Exception as e:
        log(f"下载图片出错: {e}")
        image_download(img_url, save_path, file_name)

def get_url_jpg(url,save_path,file_name):
    page_text = get_url_text(url)
    img_url = get_image_url(page_text)
    image_download(img_url, save_path,file_name)


