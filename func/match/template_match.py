from func.common import *
from func.basic import *

class t_match():
    def __init__(self,window_title,image_path):
        self.wt = window_title
        self.path = image_path


    def get_match_result(self,image,template):
        # 将图像和模板转为灰度图
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        # 使用归一化相关系数方法进行模板匹配
        result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
        return result

    def match_pic(self,name,num = 0.85,image = None):
        if image is None:
            image = get_pic(self.wt)
        template = load_image_with_zh_path(f'{self.path}{name}.png')
        height, width = template.shape[:2]
        # log(template)
        if image is None or image.size == 0:
            return None
        result = self.get_match_result(image,template)
        if result is None:
            log('匹配失败，确认图片是否存在')
            return None
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 设置一个阈值来过滤低相关度的匹配
        threshold = num
        if max_val >= threshold:
            return [max_loc[0]+width//2,max_loc[1]+height//2],round(max_val,2)
        else:
            pass
            # log('未匹配到')


    def match_pics(self,name,num = 0.85,image = None):
        if image is None:
            image = get_pic(self.wt)
        template = load_image_with_zh_path(f'{self.path}{name}.png')

        result = self.get_match_result(image,template)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 设置一个阈值来过滤低相关度的匹配
        threshold = num
        locations = np.where(result >= threshold)
        res = []
        # 打印匹配结果
        for pt in zip(*locations[::-1]):  # locations 返回的是行列坐标，zip 反转成 (x, y) 格式
            # log(f"匹配位置: {pt}, 匹配值: {result[pt[1], pt[0]]}")
            res.append({'x':int(pt[0]),'y':int(pt[1])})
        return res

    def save_pic_loc(self,name,json_path,num = 0.85):
        if not get_hwnd(self.wt):
            log(f'{self.wt}未启动')
            return None
        image = get_pic(self.wt)
        template = load_image_with_zh_path(f'{self.path}{name}.png')
        output_file = "screenshot.png"
        # cv2.imwrite(output_file, template)
        result = self.get_match_result(image, template)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 设置一个阈值来过滤低相关度的匹配
        threshold = num
        log(max_val)
        if max_val >= threshold:
            # 计算模板匹配的区域坐标
            top_left = list(max_loc)
            h, w, channels = template.shape  # 模板的高度和宽度
            bottom_right = [top_left[0] + w, top_left[1] + h]
            locs = read_json(json_path)
            locs[name] = locs.get(name, [])
            if [top_left, bottom_right] not in locs[name]:
                locs[name].append([top_left, bottom_right])
            save_json(json_path, locs)
        else:
            log("匹配失败")


    def get_pic_loc(self,name):
        while 1:
            image = get_pic(self.wt)
            template = load_image_with_zh_path(f'{self.path}{name}.png')
            cv2.imshow('123', template)
            result = self.get_match_result(image, template)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            # 设置一个阈值来过滤低相关度的匹配
            threshold = 0.85
            if max_val >= threshold:
                # 计算模板匹配的区域坐标
                top_left = list(max_loc)
                h, w, channels = template.shape  # 模板的高度和宽度
                bottom_right = [top_left[0] + w, top_left[1] + h]
                log(max_val, [top_left, bottom_right])
            else:
                log("No match found.")
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break





if __name__ == '__main__':

    # show_real_time_match()

    match = t_match('原神','image/')
    match.save_pic_loc('剧情标识2','data/img_loc.json')