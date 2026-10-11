# -*- coding: utf-8 -*-
"""裁切 ENTJ 头部/上身特写，用于核对发型。"""
import os
from PIL import Image

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
SRC = os.path.join(BASE, "assets/char/entj.png")
OUT = os.path.join(BASE, "assets/char/_gen/char_ENTJ_v2")
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGB")
print("size:", im.size)
W, H = im.size

# 依据 2:3 竖构图估：头部约占顶部 30%
head = im.crop((int(W * 0.22), int(H * 0.00), int(W * 0.85), int(H * 0.42)))
head = head.resize((head.width * 2, head.height * 2), Image.LANCZOS)
head.save(os.path.join(OUT, "hair_before.png"))
print("ok ->", os.path.join(OUT, "hair_before.png"), head.size)
