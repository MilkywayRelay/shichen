# -*- coding: utf-8 -*-
"""去掉生图右下角「AI生成 / WORKBUDDY」水印（v2：逐行估计背景）。

v1 用大核模糊估背景，会被水印自身拉高 -> 检不出浅色水印。
v2 改为：固定右下角区域，逐行取低分位数作为该行背景，亮度超出阈值即判为水印。
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

# 水印相对右下角的范围（相对比例，够宽松以便覆盖）
RX0, RY0 = 200, 100


def dewatermark(path, out, verbose=True):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    x0, y0 = w - RX0, h - RY0
    sub = a[y0:h, x0:w]
    lum = sub @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    sat = sub.max(axis=2) - sub.min(axis=2)

    rowbg = np.percentile(lum, 18, axis=1, keepdims=True)      # 每行背景亮度
    mask = (lum > rowbg + 7.5) & (sat < 34)

    m = Image.fromarray((mask * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MaxFilter(5))
    m = m.filter(ImageFilter.GaussianBlur(2.2))
    mm = (np.asarray(m).astype(np.float32) / 255.0)[..., None]

    # 逐行取"非水印像素"的中值色作为填充色
    fill = np.zeros_like(sub)
    for r in range(sub.shape[0]):
        good = ~mask[r]
        if good.sum() > 20:
            fill[r] = np.median(sub[r][good], axis=0)
        else:
            fill[r] = np.median(sub[r], axis=0)
    # 加点垂直渐变连续性：与上一行做混合
    merged = sub * (1 - mm) + fill * mm
    a[y0:h, x0:w] = merged
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(out)
    n = int(mask.sum())
    if verbose:
        print("watermark px:", n, "->", out)
    return n


if __name__ == "__main__":
    dewatermark(sys.argv[1], sys.argv[2])
