# -*- coding: utf-8 -*-
"""裁切 ISTP 各版本特写，检查服装细节。用法: istp_check.py <文件名> <前缀>"""
import os
import sys
from PIL import Image

SRC = "assets/char/istp.png"
OUT = "assets/char/_gen/char_ISTP_v2"

fname = sys.argv[1] if len(sys.argv) > 1 else "istp_v1.png"
tag = sys.argv[2] if len(sys.argv) > 2 else "v1"
path = fname if os.path.isabs(fname) else os.path.join(OUT, fname)

im = Image.open(path).convert("RGBA")
W, H = im.size
print("src =", path, "size =", im.size)

def crop(name, l, t, r, b, scale=1.0):
    box = (int(l * W), int(t * H), int(r * W), int(b * H))
    c = im.crop(box)
    if scale != 1.0:
        c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
    bg = Image.new("RGB", c.size, (235, 235, 238))
    bg.paste(c, (0, 0), c)
    p = os.path.join(OUT, name)
    bg.save(p)
    print("->", p, bg.size)

# 头部 + 肩部
crop("chk_%s_head.png" % tag, 0.30, 0.03, 0.72, 0.30, 1.6)
# 大衣上半身（肩部 / 领口 / 胸带）
crop("chk_%s_shoulder.png" % tag, 0.22, 0.12, 0.80, 0.52, 1.2)
# 大衣下摆 + 裤腿
crop("chk_%s_hem.png" % tag, 0.18, 0.45, 0.82, 0.95, 1.2)
# 左侧下摆边缘特写（原磨白区）
crop("chk_%s_edge.png" % tag, 0.45, 0.55, 0.90, 0.85, 1.8)
