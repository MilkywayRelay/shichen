# -*- coding: utf-8 -*-
"""v15 定稿「提清」管线：去灰雾 + 2x Lanczos + 多尺度 USM
纯像素处理，零设计漂移。"""
import os
import sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15", "v15_clean.png")
GEN = os.path.join(ROOT, "assets", "char", "_gen", "char_INFJ_v15")

# 可调参数
WHITE_PT = 247      # 白场：>=247 视为纯白，去掉灰雾
BLACK_PT = 10       # 黑场
R1, P1, T1 = 1.9, 95, 2     # 大半径：线稿主体
R2, P2, T2 = 0.7, 45, 1     # 小半径：微细节
SCALE = 2


def grad(im):
    a = np.asarray(im.convert("L")).astype(np.float32)
    return round(float(abs(np.diff(a, axis=0)).mean() + abs(np.diff(a, axis=1)).mean()), 2)


def levels(im, black=0, white=255):
    a = np.asarray(im).astype(np.float32)
    a = (a - black) / max(white - black, 1) * 255.0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


src = Image.open(SRC).convert("RGB")
print("源:", src.size, "锐度", grad(src))

# 只对亮部抬白场（保护线稿），并在白场附近做羽化，避免硬切
a = np.asarray(src).astype(np.float32)
t = np.clip((a - (WHITE_PT - 14)) / 14.0, 0, 1)        # 233 以下不动
a = a + (255.0 - a) * t
# 黑场轻压，提线稿对比
a = np.clip((a - BLACK_PT) / (255.0 - BLACK_PT) * 255.0, 0, 255)
img = Image.fromarray(a.astype(np.uint8))
print("去灰雾后 锐度", grad(img))

up = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS)
up = up.filter(ImageFilter.UnsharpMask(radius=R1, percent=P1, threshold=T1))
up = up.filter(ImageFilter.UnsharpMask(radius=R2, percent=P2, threshold=T2))
print("2x 后 锐度(2x坐标)", grad(up))

out = os.path.join(GEN, "v15_clarify_2x.png")
up.save(out)
print("->", out)

# 同时也存 1x 提清版（不放大，供对照/网页用）
lvl1 = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=2))
p1 = os.path.join(GEN, "v15_clarify_1x.png")
lvl1.save(p1)
print("1x 锐度", grad(lvl1), "->", p1)
