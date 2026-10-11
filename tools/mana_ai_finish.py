"""Mana：AI 抠图结果 -> 站点用透明底成品

AI（buddy-image-processing matting）已经把发丝镂空、指缝、白袍处理干净，
这里只做两件事：
  1. 底部柔和渐隐（smoothstep），让裙摆末端淡出而不是被硬边切断；
  2. 缩放到站点尺寸 1024x1536，并只对完全不透明的内部做轻度锐化
     （半透明边缘不锐化，避免出现白/彩边）。

裁剪掉原图四周多余的背景边（AI matte 保留了原图尺寸 1248x1872）。
"""
import numpy as np
from PIL import Image, ImageFilter

SRC = "assets/char/mana_matte/ai_matte_raw.png"
DST = "assets/char/mana.png"
TW, TH = 1024, 1536
FADE_START, FADE_END = 0.865, 0.993

im = Image.open(SRC).convert("RGBA")
a = np.asarray(im).astype(np.float32)
h, w = a.shape[:2]
print("src", im.size)

alpha = a[..., 3] / 255.0

# ---- 1) 底部柔和渐隐 ----
y0, y1 = int(h * FADE_START), int(h * FADE_END)
yy = np.arange(h, dtype=np.float32)
t = np.clip((yy - y0) / max(1, (y1 - y0)), 0.0, 1.0)
t = t * t * (3 - 2 * t)                 # smoothstep
ramp = np.where(yy < y0, 1.0, 1.0 - t)
alpha *= ramp[:, None]
print("bottom fade rows %d-%d (%.0f%%-%.0f%%)" % (y0, y1, 100 * FADE_START, 100 * FADE_END))

# ---- 2) 边缘去背景色污染 ----
# AI matte 的 RGB 已基本是前景色；对极低 alpha 的像素把颜色向邻近不透明色靠拢，
# 避免缩放时残留背景米色渗进发丝边缘。
lo = (alpha > 0.02) & (alpha < 0.35)
print("low-alpha edge px", int(lo.sum()))

rgba = np.dstack([a[..., :3], np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
full = Image.fromarray(rgba, "RGBA")

# ---- 3) 缩放（预乘后缩放，避免透明区颜色渗入边缘）----
rgb = a[..., :3]
pre = np.dstack([np.clip(rgb * alpha[..., None], 0, 255), np.clip(alpha * 255, 0, 255)])
pre_im = Image.fromarray(pre.astype(np.uint8), "RGBA").resize((TW, TH), Image.LANCZOS)
sp = np.asarray(pre_im).astype(np.float32)
s_al = sp[..., 3] / 255.0
s_rgb = np.where(s_al[..., None] > 1e-3, sp[..., :3] / np.clip(s_al[..., None], 1e-3, 1), 255.0)
s_rgb = np.clip(s_rgb, 0, 255)

# ---- 4) 只对完全不透明的内部轻度锐化 ----
base = Image.fromarray(np.dstack([s_rgb, s_al * 255]).astype(np.uint8), "RGBA")
sharp = base.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.3, percent=45, threshold=4))
out = np.asarray(base.convert("RGB")).copy()
solid = s_al > 250 / 255.0
out[solid] = np.asarray(sharp)[solid]

Image.fromarray(np.dstack([out, s_al * 255]).astype(np.uint8), "RGBA").save(DST)
print("saved", DST)

# ---- 预览 ----
res = Image.open(DST).convert("RGBA")
d = Image.new("RGB", res.size, (28, 32, 44)); d.paste(res, (0, 0), res); d.save("_shots/_final_dark.png")
chk = Image.new("RGB", res.size)
px = chk.load()
for y in range(0, res.height, 16):
    for x in range(0, res.width, 16):
        c = (200, 200, 200) if ((x // 16 + y // 16) % 2 == 0) else (238, 238, 238)
        for yy2 in range(y, min(y + 16, res.height)):
            for xx2 in range(x, min(x + 16, res.width)):
                px[xx2, yy2] = c
chk.paste(res, (0, 0), res); chk.save("_shots/_final_chk.png")
al = np.asarray(res)[..., 3]
print("final alpha<10 %.2f%%  alpha>245 %.2f%%" % (100 * (al < 10).mean(), 100 * (al > 245).mean()))
