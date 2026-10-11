# -*- coding: utf-8 -*-
"""Mana 手部拼合试验：把 E 的手部椭圆羽化区块贴到 N 上。
参数集中在 CFG，便于按目视结果微调。
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = r"C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
E_PATH = os.path.join(BASE, "assets/char/mana_alt/E_handfix_raw.png")
N_PATH = os.path.join(BASE, "assets/char/mana_alt/N_nofeet.png")

# ---- 可调参数 ----
DX, DY = -15, -5          # E 相对 N 的平移
# 椭圆中心/半径（N 坐标系）
CX, CY = 340, 640
RX, RY = 105, 120
ROT = -18                 # 椭圆长轴旋转（度）
FEATHER = 26
OUT = os.path.join(BASE, "assets/char/_mana_handfix.png")
PREVIEW = os.path.join(BASE, "_shots", "_handfix_result.png")
BOX = (215, 470, 500, 790)


def ellipse_mask(size, cx, cy, rx, ry, rot, feather):
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
    d.ellipse(bbox, fill=255)
    m = m.rotate(rot, center=(cx, cy), resample=Image.BICUBIC)
    m = m.filter(ImageFilter.GaussianBlur(feather / 2.0))
    return np.asarray(m).astype(np.float32) / 255.0


def main():
    aE = np.asarray(Image.open(E_PATH).convert("RGB")).astype(np.float32)
    aN = np.asarray(Image.open(N_PATH).convert("RGB")).astype(np.float32)
    h, w = aN.shape[:2]
    # 平移 E
    Es = np.roll(np.roll(aE, DY, axis=0), DX, axis=1)
    m = ellipse_mask((w, h), CX, CY, RX, RY, ROT, FEATHER)[..., None]

    # 色彩匹配：在掩膜核心（>0.85）区域把 E 的均值/方差对齐到 N
    core = (m[..., 0] > 0.85)
    for c in range(3):
        e_m, e_s = Es[..., c][core].mean(), Es[..., c][core].std() + 1e-3
        n_m, n_s = aN[..., c][core].mean(), aN[..., c][core].std() + 1e-3
        Es[..., c] = (Es[..., c] - e_m) / e_s * n_s * 0.95 + n_m

    out = aN * (1 - m) + Es * m
    out8 = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out8).save(OUT)
    x0, y0, x1, y1 = BOX
    Image.fromarray(out8[y0:y1, x0:x1]).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS).save(PREVIEW)
    print("saved", OUT, "params dx,dy=(%d,%d) center=(%d,%d) r=(%d,%d) rot=%d" % (DX, DY, CX, CY, RX, RY, ROT))


if __name__ == "__main__":
    main()
