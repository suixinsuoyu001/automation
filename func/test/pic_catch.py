import cv2
import numpy as np

class TriangleCropTool:
    def __init__(self, image_path, save_path="朝向模板.png", window_size=(800, 600)):
        self.img_full = cv2.imread(image_path)
        if self.img_full is None:
            raise FileNotFoundError("无法读取图像")

        self.clone = self.img_full.copy()
        self.save_path = save_path

        self.view_w, self.view_h = window_size
        self.img_h, self.img_w = self.img_full.shape[:2]
        self.max_x = max(0, self.img_w - self.view_w)
        self.max_y = max(0, self.img_h - self.view_h)

        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.drag_start = (0, 0)

        self.zoom_scale = 8
        self.zoom_size = 15
        self.mouse_pos = (0, 0)
        self.points = []

        cv2.namedWindow("Triangle Select")
        cv2.setMouseCallback("Triangle Select", self.mouse_event)

    def run(self):
        print("提示：点击三角形三个角点，Enter确认，ESC退出")
        while True:
            self.draw_view()
            self.draw_zoom()
            key = cv2.waitKey(10) & 0xFF
            if key in [13, 32]:  # Enter / 空格确认
                if len(self.points) == 3:
                    self.extract_triangle()
                else:
                    print("请选满3个点")
                break
            elif key == 27:  # ESC
                break
        cv2.destroyAllWindows()

    def draw_view(self):
        view = self.img_full[
            self.offset_y:self.offset_y+self.view_h,
            self.offset_x:self.offset_x+self.view_w
        ].copy()

        # 显示已点击点
        for idx, (x, y) in enumerate(self.points):
            x_rel, y_rel = x - self.offset_x, y - self.offset_y
            cv2.circle(view, (x_rel, y_rel), 3, (0, 0, 255), -1)
            if idx > 0:
                x_prev, y_prev = self.points[idx - 1]
                cv2.line(view,
                         (x_prev - self.offset_x, y_prev - self.offset_y),
                         (x_rel, y_rel),
                         (255, 0, 0), 1)
        if len(self.points) == 3:
            x0, y0 = self.points[0]
            x2, y2 = self.points[2]
            cv2.line(view,
                     (x2 - self.offset_x, y2 - self.offset_y),
                     (x0 - self.offset_x, y0 - self.offset_y),
                     (255, 0, 0), 1)

        cv2.imshow("Triangle Select", view)

    def draw_zoom(self):
        x, y = self.mouse_pos

        # 防止越界
        if not (0 <= x < self.img_w and 0 <= y < self.img_h):
            return

        x1, y1 = max(0, x - self.zoom_size), max(0, y - self.zoom_size)
        x2, y2 = min(self.img_w, x + self.zoom_size), min(self.img_h, y + self.zoom_size)
        roi = self.img_full[y1:y2, x1:x2]
        if roi.size == 0:
            return

        zoom = cv2.resize(roi, None, fx=self.zoom_scale, fy=self.zoom_scale, interpolation=cv2.INTER_NEAREST)

        # 中心点十字
        zx, zy = (x - x1) * self.zoom_scale, (y - y1) * self.zoom_scale
        cv2.drawMarker(zoom, (zx, zy), (0, 255, 0), cv2.MARKER_CROSS, markerSize=self.zoom_scale + 2)

        # 显示RGB
        b, g, r = self.img_full[y, x]
        text = f"({x},{y}) RGB=({r},{g},{b})"
        cv2.putText(zoom, text, (5, zoom.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow("Zoom", zoom)

    def mouse_event(self, event, x, y, flags, param):
        real_x, real_y = x + self.offset_x, y + self.offset_y
        self.mouse_pos = (real_x, real_y)

        if event == cv2.EVENT_LBUTTONDOWN:
            if flags & cv2.EVENT_FLAG_CTRLKEY:
                self.dragging = True
                self.drag_start = (x, y)
            elif len(self.points) < 3:
                self.points.append((real_x, real_y))
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging:
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                self.offset_x = np.clip(self.offset_x - dx, 0, self.max_x)
                self.offset_y = np.clip(self.offset_y - dy, 0, self.max_y)
                self.drag_start = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False

    def extract_triangle(self):
        if len(self.points) != 3:
            print("不满足三角形")
            return
        mask = np.zeros(self.img_full.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [np.array(self.points)], 255)

        rgba = cv2.cvtColor(self.img_full, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask

        x, y, w, h = cv2.boundingRect(np.array(self.points))
        triangle_cropped = rgba[y:y+h, x:x+w]

        cv2.imwrite(self.save_path, triangle_cropped)
        print(f"三角形图像已保存为：{self.save_path}")
        cv2.imshow("Triangle Result", triangle_cropped)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# 使用方法：
if __name__ == "__main__":
    tool = TriangleCropTool(r"E:\python\automation\games\ys\image\test1.png")
    tool.run()


