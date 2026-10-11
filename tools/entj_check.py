# -*- coding: utf-8 -*-
"""通用细节自检：裁头部特写 + 领口特写。用法：python entj_check.py <图片文件名> [标签]"""
import os
import sys
from PIL import Image

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")

name = sys.argv[1]
tag = sys.argv[2] if len(sys.argv) > 2 else "chk"
SRC = name if os.path.isabs(name) else os.path.join(G, name)

im = Image.open(SRC).convert("RGB")
W, H = im.size
print("src:", SRC)
print("size:", im.size)

head = im.crop((int(W * 0.24), 0, int(W * 0.84), int(H * 0.30)))
head = head.resize((head.width * 3, head.height * 3), Image.LANCZOS)
head.save(os.path.join(G, f"chk_{tag}_head.png"))

collar = im.crop((int(W * 0.32), int(H * 0.10), int(W * 0.78), int(H * 0.32)))
collar = collar.resize((collar.width * 3, collar.height * 3), Image.LANCZOS)
collar.save(os.path.join(G, f"chk_{tag}_collar.png"))
print("ok ->", f"chk_{tag}_head.png / chk_{tag}_collar.png")
