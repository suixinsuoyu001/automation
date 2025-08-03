from func.match.template_match import *
from PIL import Image

def feature_match(screen_gray,template_gray):
    # 初始化 SIFT
    sift = cv2.SIFT_create()

    # 检测关键点与描述符
    kp1, des1 = sift.detectAndCompute(template_gray, None)
    kp2, des2 = sift.detectAndCompute(screen_gray, None)

    if des1 is None or des2 is None:
        print("未找到特征点，无法匹配")
        exit()

    # 设置 FLANN 参数
    index_params = dict(algorithm=1, trees=10)  # algorithm=1 => KDTree for SIFT
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # KNN 匹配（每个特征点匹配两个最接近的点）
    matches = flann.knnMatch(des1, des2, k=2)

    # 应用 Lowe's Ratio Test 过滤错误匹配
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # 相似度评分：好匹配数 / 总特征数（可用 min(len(des1), len(des2)) 限定）
    total_possible = min(len(des1), len(des2))
    similarity_score = len(good_matches) / total_possible if total_possible > 0 else 0

    print(f"相似度得分（0~1，越大越相似）: {similarity_score:.4f}")

def rotate_image_clockwise(img, angle=1):
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    rotated = cv2.warpAffine(img, M, (new_w, new_h))
    return rotated


def match_ego_angle(image_path, template):
    # cv2.imshow("Detection Result", template)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    image = load_image_with_zh_path(image_path)
    # 将图像和模板转为灰度图
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    max_match_value = 0
    res = None
    for i in range(360):
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        gray_template = rotate_image_clockwise(gray_template, i)
        # 使用归一化相关系数方法进行模板匹配
        result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val > max_match_value:
            max_match_value = max_val
            res = i

    # 设置一个阈值来过滤低相关度的匹配
    return 360-res

if __name__ == '__main__':
    template = r"games\ys\image\test1.png"
    image = r"games\ys\action\朝向模板.png"
    res = match_ego_angle(image, template)

    print(res)
