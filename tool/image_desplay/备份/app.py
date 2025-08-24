from flask import Flask, render_template, send_from_directory, abort, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# 图片根目录
# IMAGE_ROOT = os.path.join(os.getcwd(), "static", "images")
IMAGE_ROOT = 'E:\images'


def get_first_images_by_directory(root):
    """遍历目录，获取每个子目录的首张图片"""
    first_images = []
    for dirpath, _, filenames in os.walk(root):
        # 只处理非根目录的子目录
        if dirpath != root:
            # 按字母排序找到第一张图片
            image_files = sorted(
                [f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            )
            if image_files:
                relative_path = os.path.relpath(dirpath, root).replace("\\", "/")
                first_images.append({
                    "dir_path": relative_path,  # 子目录路径
                    "first_image": f"{relative_path}/{image_files[0]}",  # 第一个图片路径
                    "dir_name": relative_path.replace("/", " - ")  # 目录名显示
                })
    return first_images


def get_images_in_directory(directory):
    """获取指定目录下的所有图片"""
    images = []
    if os.path.exists(directory):
        images = sorted(
            [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        )
    return images


@app.route('/')
def index():
    """首页显示每个目录的首张图片"""
    first_images = get_first_images_by_directory(IMAGE_ROOT)
    return render_template("index.html", first_images=first_images)


@app.route('/gallery/<path:dir_path>')
def gallery(dir_path):
    """展示指定目录的所有图片"""
    full_dir_path = os.path.join(IMAGE_ROOT, dir_path)
    if not os.path.exists(full_dir_path):
        abort(404, description="Directory not found")  # 返回 404 错误
    images = get_images_in_directory(full_dir_path)
    images = sorted(images, key=lambda x: int(os.path.splitext(x)[0]))
    if not images:
        return render_template("gallery.html", images=[], dir_path=dir_path, error="No images found in this directory.")
    return render_template("gallery.html", images=images, dir_path=dir_path)


@app.route('/static/images/<path:filename>')
def serve_image(filename):
    """提供静态图片"""
    return send_from_directory(IMAGE_ROOT, filename)


@app.route('/view_image')
def view_image():
    """展示单张图片的大图并提供上下翻页功能"""
    dir_path = request.args.get('dir_path')
    index = int(request.args.get('index',1))
    full_dir_path = os.path.join(IMAGE_ROOT, dir_path)
    if not os.path.exists(full_dir_path):
        abort(404, description="Directory not found")

    images = get_images_in_directory(full_dir_path)
    images = sorted(images, key=lambda x: int(os.path.splitext(x)[0]))
    if not images:
        abort(404, description="No images found in this directory")
    if index < 0 or index >= len(images):
        index = 0
    return render_template('view_image.html', dir_path=dir_path, images=images, index=index)


# 存储点击记录
click_logs = []
#
@app.route('/log_click', methods=['POST'])
def log_click():
    data = request.json

    url = data.get('src')
    timestamp = data.get('timestamp')
    ip_address = request.remote_addr
    print(data)
    if data.get('type') == 'open':
        click_logs.append(data.get('src'))
        print('1', click_logs)
    if data.get('type') == 'change':
        click_logs.append(f"{data.get('src').split('&index=')[0]}&index={data.get('index')}")
        print('2', click_logs)
    if data.get('type') == 'close':
        if click_logs:
            click_logs.reverse()  # 先反转列表
            click_logs.remove(data.get('src'))  # 删除第一个 'a'（反转后为原列表中的最后一个 'a'）
            click_logs.reverse()  # 再反转回来
            print('3', click_logs)
    # 将点击信息存储到日志中
    app.logger.info(f"Page clicked: {url}, IP: {ip_address}, Time: {timestamp}")

    return jsonify({"status": "success"}), 200

@app.route('/view_click_logs')
def view_click_logs():
    return jsonify(click_logs)


if __name__ == '__main__':
    app.run(debug=True)
