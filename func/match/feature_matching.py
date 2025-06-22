from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pyautogui,cv2,time
from PIL import Image, ImageDraw, ImageFont

# 使用 SIFT 特征点检测器
sift = cv2.SIFT_create()

class target_detection():
    def __init__(self,path):
        self.path = path
        self.required_matches = 5



    def load_image_with_zh_path(self, file_path):
        """使用 cv2.imdecode 读取中文路径图片"""
        # 使用二进制方式读取文件
        with open(file_path, 'rb') as f:
            binary_data = f.read()
        # 将二进制数据转换为 NumPy 数组
        image_data = np.frombuffer(binary_data, dtype=np.uint8)
        # 解码为图像
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if image is None:
            print(f"无法加载图片: {file_path}")
            return None
        # image = cv2.resize(image, None, fx=0.9, fy=0.9, interpolation=cv2.INTER_LINEAR)

        return image

    def match_features(self, screen, templates):

        required_matches = self.required_matches
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        def process_template(template_name, screen, screen_gray, sift, required_matches, path):
            try:
                template_path = f'{path}/{template_name}.png'
                # 读取模板图像
                template = self.load_image_with_zh_path(template_path)
                if template is None:
                    print(f"模板图片未找到: {template_path}")
                    return None

                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # 检测并计算关键点和描述符
                kp1, des1 = sift.detectAndCompute(template_gray, None)
                kp2, des2 = sift.detectAndCompute(screen_gray, None)

                if des1 is None or des2 is None:
                    return None

                # FLANN参数设置
                index_params = dict(algorithm=1, trees=10)
                search_params = dict(checks=50)
                flann = cv2.FlannBasedMatcher(index_params, search_params)
                matches = flann.knnMatch(des1, des2, k=2)

                # 应用 Lowe 的比率测试过滤掉不好的匹配
                good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

                # 绘制所有匹配点（可选）
                for m in good_matches:
                    if m.distance < 50:
                        x, y = kp2[m.trainIdx].pt
                        cv2.circle(screen, (int(x), int(y)), 5, (255, 0, 0), -1)

                # 如果匹配点足够多
                if len(good_matches) >= required_matches:
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    # 计算变换矩阵
                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                    if M is not None:
                        h, w = template_gray.shape
                        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                        dst = cv2.perspectiveTransform(pts, M)

                        # 计算框内匹配点的平均距离作为置信度
                        # 先计算所有的匹配点是否在目标框内
                        box_points = np.int32(dst).reshape(-1, 2)
                        detected_matches = []

                        for m in good_matches:
                            x, y = kp2[m.trainIdx].pt
                            # 判断匹配点是否在目标框内
                            if cv2.pointPolygonTest(box_points, (x, y), False) >= 0:
                                detected_matches.append(m)

                        # 按距离排序，选择前 10 个最小的匹配点
                        detected_matches_sorted = sorted(detected_matches, key=lambda x: x.distance)[:10]

                        # 计算置信度：基于前 10 个匹配点的距离
                        if detected_matches_sorted:
                            avg_distance = np.mean([m.distance for m in detected_matches_sorted])
                            confidence = 100 - avg_distance
                        else:
                            confidence = 0

                        return (dst, confidence, template_name)
            except Exception as e:
                print(f"处理模板 {template_name} 时出错: {e}")
                return None

        def match_templates_concurrently(templates, screen, screen_gray, sift, required_matches, path):
            detected_boxes = []
            with ThreadPoolExecutor() as executor:
                # 提交所有模板的任务
                future_to_template = {
                    executor.submit(process_template, template_name, screen, screen_gray, sift, required_matches,
                                    path): template_name
                    for template_name in templates
                }

                # 收集任务结果
                for future in future_to_template:
                    result = future.result()
                    if result is not None:
                        detected_boxes.append(result)

            return detected_boxes

        detected_boxes = match_templates_concurrently(
            templates, screen, screen_gray, sift, required_matches, self.path
        )

        detected_boxes = self.non_max_suppression(detected_boxes)

        screen_pil = Image.fromarray(cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))

        # 创建一个绘制对象
        draw = ImageDraw.Draw(screen_pil)

        font_path = r"C:\Windows\Fonts\msyh.ttc"  # 微软雅黑
        font = ImageFont.truetype(font_path, 30)

        for dst, confidence,template_name in detected_boxes:

            if confidence > 40:
                box_points = np.int32(dst).reshape(-1, 2)
                x_min = min(box_points[:, 0])
                y_min = min(box_points[:, 1])
                x_max = max(box_points[:, 0])
                y_max = max(box_points[:, 1])
                # 绘制矩形框，(x_min, y_min) 是左上角，(x_max, y_max) 是右下角
                draw.rectangle([x_min, y_min, x_max, y_max], outline="yellow", width=3)
                # 计算左上角位置
                text_pos = tuple(np.int32(dst[0][0]))  # 左上角的点

                # 绘制模板名称和置信度
                draw.text(text_pos, f"{template_name} {confidence:.2f}%", font=font, fill=(0, 255, 0))
                # 绘制目标框

        # 转回 OpenCV 格式
        screen = cv2.cvtColor(np.array(screen_pil), cv2.COLOR_RGB2BGR)

        return screen

    def non_max_suppression(self, detected_boxes, overlap_thresh=0.3):

        if len(detected_boxes) == 0:
            return []

        # 将框的坐标转换为矩形的左上和右下点
        boxes = np.array([cv2.boundingRect(np.int32(box)) for box, confidence,template_name in detected_boxes])
        confidences = np.array([confidence for dst, confidence, template_name in detected_boxes])

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = x1 + boxes[:, 2]
        y2 = y1 + boxes[:, 3]
        # 计算框面积并排序
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = confidences.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)

            overlap = (w * h) / areas[order[1:]]
            order = order[np.where(overlap <= overlap_thresh)[0] + 1]

        return [detected_boxes[i] for i in keep]

    def capture_and_process(self,screen_region, templates):
        # t = time.time()
        # 截取指定屏幕区域
        screenshot = get_pic('原神')
        x, y, w, h = screen_region
        screenshot = screenshot[y:y + h, x:x + w]  # 裁剪图像

        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        # print(f'处理图片格式 {time.time() - t}')
        # t = time.time()
        # 进行特征点匹配
        processed_screen = self.match_features(screenshot, templates)
        # print(f'处理图片特征 {time.time() - t}')
        return processed_screen

    def set_window_topmost(self,window_name):
        """确保窗口始终保持在最前端"""
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    def show_real_time_match(self,template_paths, region=(0, 0, 800, 600)):
        window_name = "Processed Screen"
        while True:

            t0 = time.time()
            # 获取并处理当前屏幕区域
            processed_screen = self.capture_and_process(region, template_paths)
            # image = cv2.imread('screenshot2.png')
            # 显示处理后的图像
            cv2.imshow(window_name, processed_screen)
            self.set_window_topmost(window_name)  # 设置窗口置顶

            # 退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            end_time = time.time()
            print(f'总用时 {time.time() - t0}')
            # 控制每秒处理一次
            time.sleep(0.2)

        cv2.destroyAllWindows()

if __name__ == '__main__':
    td = target_detection(r'/image')
    # 输入模板路径列表
    # template_paths = ["玛薇卡",'希诺宁','钟离','玛拉妮']
    template_paths = ["菜单"]
    # 截图区域左上 (500, 0) 到 1000x1200，按需调整
    region = (34, 20, 82, 90)
    # 启动实时识别并显示匹配结果
    td.show_real_time_match(template_paths, region)
