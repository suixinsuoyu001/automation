import onnxruntime as ort
import numpy as np
import cv2
import json
from func.get_pic import *

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114)):
    shape = img.shape[:2]  # h, w
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = (int(shape[1] * r), int(shape[0] * r))  # new w,h
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # padding w,h
    dw /= 2  # divide padding into 2 sides
    dh /= 2

    img_resized = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    img_padded = cv2.copyMakeBorder(img_resized, int(dh), int(dh), int(dw), int(dw),
                                    cv2.BORDER_CONSTANT, value=color)
    return img_padded, r, dw, dh

class BigTreeYoloPredictor:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape  # [1, 3, H, W]

    def preprocess(self, image: np.ndarray):
        img, ratio, dw, dh = letterbox(image, (self.input_shape[2], self.input_shape[3]))
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)  # HWC to CHW
        img = np.expand_dims(img, axis=0)  # add batch dim
        return img, ratio, dw, dh

    def detect(self, image: np.ndarray, conf_threshold=0.4):
        input_tensor, ratio, dw, dh = self.preprocess(image)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        output = outputs[0]  # (5, 8400)

        predictions = output.T  # (8400, 5)

        # 四舍五入padding，保证整数
        top, left = int(round(dh)), int(round(dw))

        boxes = []
        for det in predictions:
            cx, cy, w, h, conf = det[:5].flatten().astype(float).tolist()
            if conf < conf_threshold:
                continue

            # 先还原至原始图比例和坐标（减padding，除ratio）
            cx = (cx - left) / ratio
            cy = (cy - top) / ratio
            w /= ratio
            h /= ratio

            # 如果x,y是中心坐标，转成左上角坐标
            x1 = int(cx - w / 2)
            y1 = int(cy - h / 2)
            x2 = int(cx + w / 2)
            y2 = int(cy + h / 2)

            boxes.append({
                'class_id': 0,
                'confidence': float(conf),
                'box': [x1, y1, x2, y2]
            })

        return boxes

    def draw_boxes(self, image: np.ndarray, boxes: list, class_names: list = None):
        for item in boxes:
            x1, y1, x2, y2 = item['box']
            label = str(item['class_id'])
            if class_names and item['class_id'] < len(class_names):
                label = class_names[item['class_id']]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"{label} {item['confidence']:.2f}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return image


def model_match_pic(image,is_show = False):
    model_path = "games/ys/match/big_tree.onnx"
    predictor = BigTreeYoloPredictor(model_path)
    detections = predictor.detect(image)
    if is_show:
        image = image.copy()
        image_with_boxes = predictor.draw_boxes(image, detections)
        cv2.imshow("Detection Result", image_with_boxes)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    if detections:
        best_box = max(detections, key=lambda x: x['confidence'])
        return best_box['box'],best_box['confidence']

if __name__ == "__main__":

    image = get_pic("原神")
    print(model_match_pic(image,is_show= True))

