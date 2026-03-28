import cv2
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
from collections import defaultdict
import os

class OfficeObjectDetector:
    def __init__(self, models_base_path="models/"):
        self.models_base = Path(models_base_path)
        self.models = {}
        self.colors = {}
        # self._load_models()
        self._setup_colors()

        self._load_keyboard_only()  # 只加载键盘模型

    def _load_keyboard_only(self):
        """只加载键盘模型"""
        model_path = self.models_base / "keyboard.pt"

        if model_path.exists():
            try:
                self.models['keyboard'] = YOLO(str(model_path))
                print(f"✅ 已加载键盘识别模型")
            except Exception as e:
                print(f"❌ 加载键盘模型失败: {e}")
                # 如果没有模型，创建空的模型字典
                self.models = {}
        else:
            print(f"⚠️ 键盘模型不存在: {model_path}")
            print("💡 请将 keyboard.pt 文件放入 models/ 目录")

    # def _load_models(self):
    #     """加载所有物品检测模型"""
    #     model_config = {
    #         'keyboard': 'keyboard.pt',
    #         'pen': 'pen.pt',
    #         'cup': 'cup.pt',
    #         'mouse': 'mouse.pt',
    #         'phone': 'phone.pt',
    #         'laptop': 'laptop.pt'
    #     }
    #
    #     for item, filename in model_config.items():
    #         model_path = self.models_base / filename
    #         if model_path.exists():
    #             self.models[item] = YOLO(str(model_path))
    #             print(f"✅ 已加载模型: {item}")
    #         else:
    #             print(f"⚠️  模型不存在: {filename}")

    # def _setup_colors(self):
    #     """为每个物品类别设置不同的颜色"""
    #     # 使用matplotlib的颜色映射
    #     cmap = plt.cm.get_cmap('tab20c')
    #     items = list(self.models.keys())
    #
    #     for idx, item in enumerate(items):
    #         # 转换为BGR格式（OpenCV使用）
    #         rgb_color = cmap(idx / max(len(items), 1))[:3]
    #         bgr_color = (int(rgb_color[2] * 255),
    #                      int(rgb_color[1] * 255),
    #                      int(rgb_color[0] * 255))
    #         self.colors[item] = bgr_color

    def _setup_colors(self):
        """设置键盘的特定颜色"""
        if 'keyboard' in self.models:
            # 键盘使用橙色
            self.colors['keyboard'] = (0, 165, 255)  # BGR格式的橙色
        else:
            self.colors = {}


    # def detect(self, image_path):
    #     """
    #     检测图片中的办公室物品
    #     返回: (标注后的图片, 检测结果列表, 统计信息)
    #     """
    #     img = cv2.imread(str(image_path))
    #     if img is None:
    #         raise ValueError(f"无法读取图片: {image_path}")
    #
    #     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #     result_img = img.copy()  # 在原始图片上标注
    #
    #     all_detections = []
    #     stats = defaultdict(int)
    #
    #     # 每个模型分别检测
    #     for item, model in self.models.items():
    #         results = model(img_rgb, conf=0.3, iou=0.5, verbose=False)
    #
    #         for result in results:
    #             if result.boxes is not None:
    #                 for box in result.boxes:
    #                     x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    #                     conf = float(box.conf[0])
    #
    #                     # 绘制边界框
    #                     color = self.colors.get(item, (0, 255, 0))
    #                     cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
    #
    #                     # 绘制标签背景
    #                     label = f"{item} {conf:.2f}"
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
    #                         'item': item,
    #                         'confidence': round(conf, 3),
    #                         'bbox': [x1, y1, x2, y2],
    #                         'area': (x2 - x1) * (y2 - y1)
    #                     }
    #                     all_detections.append(detection)
    #                     stats[item] += 1
    #
    #     return result_img, all_detections, dict(stats)

    def detect(self, image_path):
        """
        检测图片中的键盘
        返回: (标注后的图片, 检测结果列表, 统计信息)
        """
        if not os.path.exists(image_path):
            raise ValueError(f"图片文件不存在: {image_path}")

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        result_img = img.copy()  # 在原始图片上标注
        all_detections = []
        stats = {}

        # 检查是否有加载模型
        if not self.models:
            print("⚠️ 没有可用的模型，返回空白结果")
            return result_img, all_detections, stats

        # 只使用键盘模型进行检测
        for item, model in self.models.items():
            try:
                results = model(img, conf=0.3, iou=0.5, verbose=False)
            except Exception as e:
                print(f"⚠️ 模型检测失败: {e}")
                continue

            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])

                        # 绘制边界框
                        color = self.colors.get(item, (0, 165, 255))  # 橙色
                        cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)

                        # 绘制标签
                        label = f"keyboard {conf:.2f}"
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
                        stats[item] = stats.get(item, 0) + 1

        return result_img, all_detections, stats

    def save_result_image(self, result_img, output_path):
        """保存结果图片"""
        cv2.imwrite(str(output_path), result_img)
        return output_path