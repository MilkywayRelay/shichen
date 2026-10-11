# -*- coding: utf-8 -*-
"""
ISTP 虹膜改为「威士忌色」——确定性调色，不改造型。
依据：角色形象/ISTP.md  瞳孔为威士忌般的深赤褐色，外层一圈更淡的焦糖色环纹。
"""
import numpy as np
from PIL import Image

SRC = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen/assets/char/istp.png"

# 左右眼：中心 + 半轴（axis-aligned ellipse），按头部微倾给一点旋转
EYES = [
    # (cx, cy, rx, ry, rot_deg)
    (316.5, 141.0, 11.5, 6.6, -8.0),
    (369.5, 127.5, 11.5, 6.6, -8.0),
]

DEEP  = np.array([52.0, 22.0, 12.0])    # 深赤褐（暗部）
AMBER = np.array([206.0, 148.0, 78.0])  # 焦糖色环纹（亮部）

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.float32)
H, W, _ = a.shape
L = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)   # 亮度

yy, xx = np.mgrid[0:H, 0:W]

w_total = np.zeros((H, W), dtype=np.float32)
for cx, cy, rx, ry, rot in EYES:
    th = np.deg2rad(rot)
    dx, dy = xx - cx, yy - cy
    u = (dx * np.cos(th) + dy * np.sin(th)) / rx
    v = (-dx * np.sin(th) + dy * np.cos(th)) / ry
    r = np.sqrt(u * u + v * v)
    # 椭圆内为 1，边缘 0.78~1.0 羽化
    ell = np.clip((1.0 - r) / 0.22, 0.0, 1.0)

    # 亮度带通：排除瞳孔/睫毛（过暗）与高光/眼白（过亮）
    band = np.clip((L - 26.0) / 34.0, 0.0, 1.0) * np.clip((206.0 - L) / 46.0, 0.0, 1.0)
    w_total = np.maximum(w_total, ell * band)

# 目标色：随亮度在深赤褐 → 焦糖之间插值，保留原有明暗结构
t = np.clip((L - 38.0) / 92.0, 0.0, 1.0)[..., None]
target = DEEP[None, None, :] * (1.0 - t) + AMBER[None, None, :] * t

STRENGTH = 0.88
w = (w_total * STRENGTH)[..., None]
out = a * (1.0 - w) + target * w

res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
res.save(SRC)
print("done ->", SRC)

# 生成放大对比图
crop = (280, 105, 405, 165)
before = im.crop(crop).resize(((crop[2]-crop[0])*7, (crop[3]-crop[1])*7), Image.LANCZOS)
after  = res.crop(crop).resize(((crop[2]-crop[0])*7, (crop[3]-crop[1])*7), Image.LANCZOS)
cmp = Image.new("RGB", (before.width, before.height*2 + 12), (255, 255, 255))
cmp.paste(before, (0, 0)); cmp.paste(after, (0, before.height + 12))
cmp.save(r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen/assets/char/_cmp_eyes.png")
print("cmp saved")
