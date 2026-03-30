import cv2
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
from collections import defaultdict
import os

class OfficeObjectDetector:
    """
    办公室物品检测器
    可以检测图片中的键盘、笔、杯子、鼠标、手机和笔记本电脑
    支持加载多个模型进行检测
    默认加载所有模型
    """
    def __init__(self, models_base_path="models/"):
        """
        初始化办公室物品检测器
        Author:
        Args:
            models_base_path(str): 模型文件夹路径
        """
        if models_base_path is None:
            # 获取项目根目录（OfficeVision 项目的根目录）
            project_root = Path(__file__).parent.parent.parent
            self.models_base = project_root / 'models'
        else:
            self.models_base = Path(models_base_path)

        self.models = {}
        self.colors = {}
        self._load_models()
        self._setup_colors()

    def _load_models(self):
        """
        加载所有物品检测模型
        Author:
        Returns:
            None

        """
        model_config = {
            'keyboard': 'keyboard.pt',
            'chair': 'chair.pt',
            'table': 'table.pt',
            'person': 'person.pt',
            'phone': 'phone.pt',
            'laptop': 'laptop.pt'
        }

        for item, filename in model_config.items():
            model_path = self.models_base / filename
            if model_path.exists():
                self.models[item] = YOLO(str(model_path))
                print(f"✅ 已加载模型: {item}")
            else:
                print(f"⚠️  模型不存在: {filename}")

    def _setup_colors(self):
        """
        设置每个物品类别的颜色
        Author:
        Returns:
            None

        """
        # 使用matplotlib的颜色映射
        cmap = plt.cm.get_cmap('tab20c')
        items = list(self.models.keys())

        for idx, item in enumerate(items):
            # 转换为BGR格式（OpenCV使用）
            rgb_color = cmap(idx / max(len(items), 1))[:3]
            bgr_color = (int(rgb_color[2] * 255),
                         int(rgb_color[1] * 255),
                         int(rgb_color[0] * 255))
            self.colors[item] = bgr_color

    def detect(self, image_path):
        """
        检测图片中的办公室物品
        Author:
        Args:
            image_path: 图片路径

        Returns:
            (标注后的图片, 检测结果列表, 统计信息)

        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result_img = img.copy()  # 在原始图片上标注

        all_detections = []
        stats = defaultdict(int)

        # 每个模型分别检测
        for item, model in self.models.items():
            results = model(img_rgb, conf=0.3, iou=0.5, verbose=False)

            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])

                        # 绘制边界框
                        color = self.colors.get(item, (0, 255, 0))
                        cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)

                        # 绘制标签背景
                        label = f"{item} {conf:.2f}"
                        (text_width, text_height), baseline = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )

                        # 标签背景框
                        cv2.rectangle(result_img,
                                      (x1, y1 - text_height - 10),
                                      (x1 + text_width, y1),
                                      color, -1)

                        # 标签文字
                        cv2.putText(result_img, label,
                                    (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                    (255, 255, 255), 2)

                        # 记录检测结果
                        detection = {
                            'item': item,
                            'confidence': round(conf, 3),
                            'bbox': [x1, y1, x2, y2],
                            'area': (x2 - x1) * (y2 - y1)
                        }
                        all_detections.append(detection)
                        stats[item] += 1

        return result_img, all_detections, dict(stats)


    # def detect_laptop_only(self, image_path):
    #     """
    #     仅检测图片中的笔记本电脑
    #     Author:
    #     Args:
    #         image_path: 图片路径
    #
    #     Returns:
    #         (标注后的图片，检测结果列表，统计信息)
    #
    #     """
    #     img = cv2.imread(str(image_path))
    #     if img is None:
    #         raise ValueError(f"无法读取图片：{image_path}")
    #
    #     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #     result_img = img.copy()
    #
    #     all_detections = []
    #     stats = defaultdict(int)
    #
    #     # 只使用 laptop 模型检测
    #     if 'laptop' in self.models:
    #         model = self.models['laptop']
    #         results = model(img_rgb, conf=0.3, iou=0.5, verbose=False)
    #
    #         for result in results:
    #             if result.boxes is not None:
    #                 for box in result.boxes:
    #                     x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    #                     conf = float(box.conf[0])
    #
    #                     # 绘制边界框
    #                     color = self.colors.get('laptop', (0, 255, 0))
    #                     cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
    #
    #                     # 绘制标签背景
    #                     label = f"laptop {conf:.2f}"
    #                     (text_width, text_height), baseline = cv2.getTextSize(
    #                         label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    #                     )
    #
    #                     # 标签背景框
    #                     cv2.rectangle(result_img,
    #                                   (x1, y1 - text_height - 10),
    #                                   (x1 + text_width, y1),
    #                                   color, -1)
    #
    #                     # 标签文字
    #                     cv2.putText(result_img, label,
    #                                 (x1, y1 - 5),
    #                                 cv2.FONT_HERSHEY_SIMPLEX, 0.6,
    #                                 (255, 255, 255), 2)
    #
    #                     # 记录检测结果
    #                     detection = {
    #                         'item': 'laptop',
    #                         'confidence': round(conf, 3),
    #                         'bbox': [x1, y1, x2, y2],
    #                         'area': (x2 - x1) * (y2 - y1)
    #                     }
    #                     all_detections.append(detection)
    #                     stats['laptop'] += 1
    #
    #     return result_img, all_detections, dict(stats)

    def save_result_image(self, result_img, output_path):
        """
        保存结果图片
        Author:
        Args:
            result_img: 结果图片
            output_path: 输出图片路径

        Returns:
            输出图片路径

        """
        cv2.imwrite(str(output_path), result_img)
        return output_path

    def detect_with_models(self, image_path, model_names):
        """
        使用指定的模型检测图片中的物品
        Author: Young
        Args:
            image_path: 图片路径
            model_names: 要使用的模型名称列表，如 ['laptop', 'keyboard']

        Returns:
            (标注后的图片，检测结果列表，统计信息)

        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"无法读取图片：{image_path}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result_img = img.copy()

        all_detections = []
        stats = defaultdict(int)

        # 只使用指定的模型检测
        for item_name in model_names:
            if item_name not in self.models:
                continue

            model = self.models[item_name]
            results = model(img_rgb, conf=0.3, iou=0.5, verbose=False)

            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])

                        # 绘制边界框
                        color = self.colors.get(item_name, (0, 255, 0))
                        cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)

                        # 绘制标签背景
                        label = f"{item_name} {conf:.2f}"
                        (text_width, text_height), baseline = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )

                        # 标签背景框
                        cv2.rectangle(result_img,
                                      (x1, y1 - text_height - 10),
                                      (x1 + text_width, y1),
                                      color, -1)

                        # 标签文字
                        cv2.putText(result_img, label,
                                    (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                    (255, 255, 255), 2)

                        # 记录检测结果
                        detection = {
                            'item': item_name,
                            'confidence': round(conf, 3),
                            'bbox': [x1, y1, x2, y2],
                            'area': (x2 - x1) * (y2 - y1)
                        }
                        all_detections.append(detection)
                        stats[item_name] += 1

        return result_img, all_detections, dict(stats)