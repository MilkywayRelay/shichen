# -*- coding: utf-8 -*-
from PIL import Image
import sys, os

src = sys.argv[1] if len(sys.argv) > 1 else "assets/char/mana.png"
tag = sys.argv[2] if len(sys.argv) > 2 else "z"
im = Image.open(src).convert("RGBA")
w, h = im.size
print("src", src, "size", im.size)

# 手/前伸臂区域
box = (int(w * 0.02), int(h * 0.24), int(w * 0.50), int(h * 0.58))
c = im.crop(box)
c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
c.save("_shots/_%s_hand.png" % tag)

# 光环 / 头部区域
box2 = (int(w * 0.16), 0, int(w * 0.90), int(h * 0.20))
c2 = im.crop(box2)
c2 = c2.resize((c2.width * 3, c2.height * 3), Image.LANCZOS)
c2.save("_shots/_%s_halo.png" % tag)

# 右侧裙摆
box3 = (int(w * 0.55), int(h * 0.45), w, int(h * 0.90))
c3 = im.crop(box3)
c3 = c3.resize((c3.width * 2, c3.height * 2), Image.LANCZOS)
c3.save("_shots/_%s_skirt.png" % tag)
print("done")
