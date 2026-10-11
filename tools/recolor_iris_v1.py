# -*- coding: utf-8 -*-
"""ISTP(v1) 虹膜 -> 威士忌色（深赤褐 + 焦糖环纹）。确定性调色，不改造型。"""
import numpy as np
from PIL import Image

SRC = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen/assets/char/v1/istp.png"
SRC_READ = r"C:/Users/admin/.workbuddy/blobs/e5/e52bb3a9244cf414352ff2e9882000aef249202a15035622c7377bfd7838400a.png"

# (cx, cy, rx, ry, rot_deg)
EYES = [
    (516.0, 191.5, 13.5, 9.5, 0.0),
    (568.0, 190.5, 13.5, 9.5, 0.0),
]

DEEP  = np.array([70.0, 34.0, 16.0])    # 深赤褐
AMBER = np.array([200.0, 152.0, 88.0])  # 焦糖

im = Image.open(SRC_READ).convert("RGB")
orig = im.copy()
a = np.asarray(im).astype(np.float32)
H, W, _ = a.shape
L = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
yy, xx = np.mgrid[0:H, 0:W]

# 肤色排除：暖色皮肤 R-G 明显为正，虹膜（灰绿/淡青）则接近 0 或为负
rg = a[:, :, 0] - a[:, :, 1]
not_skin = np.clip((12.0 - rg) / 10.0, 0.0, 1.0)

w = np.zeros((H, W), dtype=np.float32)
for cx, cy, rx, ry, rot in EYES:
    th = np.deg2rad(rot)
    dx, dy = xx - cx, yy - cy
    u = (dx * np.cos(th) + dy * np.sin(th)) / rx
    v = (-dx * np.sin(th) + dy * np.cos(th)) / ry
    r = np.sqrt(u * u + v * v)
    ell = np.clip((1.0 - r) / 0.26, 0.0, 1.0)
    band = np.clip((L - 60.0) / 50.0, 0.0, 1.0) * np.clip((215.0 - L) / 45.0, 0.0, 1.0)
    w = np.maximum(w, ell * band * not_skin)

t = np.clip((L - 60.0) / 140.0, 0.0, 1.0)[..., None]
target = DEEP[None, None, :] * (1.0 - t) + AMBER[None, None, :] * t

STRENGTH = 0.85
wm = (w * STRENGTH)[..., None]
out = a * (1.0 - wm) + target * wm
res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
res.save(SRC)

crop = (420, 150, 625, 225)
S = 6
before = orig.crop(crop).resize(((crop[2]-crop[0])*S, (crop[3]-crop[1])*S), Image.LANCZOS)
after  = res.crop(crop).resize(((crop[2]-crop[0])*S, (crop[3]-crop[1])*S), Image.LANCZOS)
cmp = Image.new("RGB", (before.width, before.height*2 + 14), (255, 255, 255))
cmp.paste(before, (0, 0)); cmp.paste(after, (0, before.height + 14))
cmp.save(r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen/assets/char/v1/_cmp_eyes.png")
print("done")
