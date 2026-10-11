# -*- coding: utf-8 -*-
"""检查 ENTJ 新版的尺寸、头部刘海、领口衬衫细节。"""
import os
from PIL import Image

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
G = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
SRC = os.path.join(G, "Keep_EVERYTHING_identical_to_t_2026-10-11T11-47-56.png")

im = Image.open(SRC).convert("RGB")
W, H = im.size
print("size:", im.size)

head = im.crop((int(W * 0.24), 0, int(W * 0.84), int(H * 0.30)))
head = head.resize((head.width * 3, head.height * 3), Image.LANCZOS)
head.save(os.path.join(G, "check_head_v4.png"))
print("head ->", head.size)

collar = im.crop((int(W * 0.32), int(H * 0.10), int(W * 0.78), int(H * 0.30)))
collar = collar.resize((collar.width * 3, collar.height * 3), Image.LANCZOS)
collar.save(os.path.join(G, "check_collar_v4.png"))
print("collar ->", collar.size)
