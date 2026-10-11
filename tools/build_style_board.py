# -*- coding: utf-8 -*-
"""识尘 · 立绘风格锚板生成器
把已定稿立绘拼成一张参考板（含角色名 + 锚色卡），
用途：① 人肉核对一致性 ② 直接当参考图喂给生图模型。
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "C:/Users/admin/WorkBuddy/2026-09-29-23-06-03/shichen"
OUT = os.path.join(BASE, "docs/风格锚板_style_ref.png")

# (相对路径, 标签, [锚色...])
ITEMS = [
    ("assets/char/isfj.png", "ISFJ · 档案员", ["#16233F", "#EDE6DA", "#C08A46"]),
    ("assets/char/enfp.png", "ENFP · 心理医生", ["#B5533A", "#6E8C8A", "#4A5540"]),
    ("assets/char/entj.png", "ENTJ · 策划", ["#3B2E4A", "#D8D2CC", "#9A94A8"]),
    ("assets/char/istp.png", "ISTP · 猎手", ["#2A2E2C", "#B03A38", "#9A7B3A"]),
    ("assets/char/mana.png", "Mana · 引导者", ["#F2EFEA", "#E0703A", "#D9CBB8"]),
    ("assets/char/_gen/char_INFJ_v19/v19b_skin_graft.png", "INFJ · 行动专员 ★定稿", ["#EFECE6", "#8B1F22", "#6E8B63"]),
    ("_deliver/立绘概念稿_ESTJ_法律部长.png", "ESTJ · 法律部长 (概念稿)", ["#2E3540", "#BFA46A", "#C9CDD4"]),
    ("_deliver/立绘概念稿_INTJ_首领.png", "INTJ · 首领 (概念稿)", ["#14131A", "#C9A227", "#6B4E9E"]),
]

COLS = 4
IMGH = 760          # 统一图高
GAP = 34            # 格间距
PAD = 40            # 板边距
LABEL_H = 74        # 每格底部标签区高

FONT_PATH = "C:/Windows/Fonts/msyh.ttc"


def load_white(path, h):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    w = max(1, int(im.width * h / im.height))
    return im.resize((w, h), Image.LANCZOS)


def main():
    imgs = []
    for rel, label, colors in ITEMS:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            print("!! missing:", p)
            continue
        imgs.append((load_white(p, IMGH), label, colors))

    cell_w = max(im.width for im, _, _ in imgs) + 20
    cell_h = IMGH + LABEL_H
    rows = (len(imgs) + COLS - 1) // COLS
    W = PAD * 2 + COLS * cell_w + (COLS - 1) * GAP
    H = PAD * 2 + rows * cell_h + (rows - 1) * GAP

    board = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(board)
    f_label = ImageFont.truetype(FONT_PATH, 30)
    f_sub = ImageFont.truetype(FONT_PATH, 22)

    for i, (im, label, colors) in enumerate(imgs):
        r, c = divmod(i, COLS)
        x0 = PAD + c * (cell_w + GAP)
        y0 = PAD + r * (cell_h + GAP)
        # 细边框
        d.rectangle([x0 - 1, y0 - 1, x0 + cell_w, y0 + IMGH], outline=(228, 228, 230), width=1)
        # 图居中
        ix = x0 + (cell_w - im.width) // 2
        board.paste(im, (ix, y0))
        # 标签区
        ty = y0 + IMGH + 14
        d.text((x0 + 4, ty), label, font=f_label, fill=(38, 38, 42))
        # 锚色卡
        dot_x = x0 + cell_w - 4 - (len(colors) * 30) + 8
        for col in colors:
            rgb = tuple(int(col[j:j + 2], 16) for j in (1, 3, 5))
            d.ellipse([dot_x, ty + 6, dot_x + 22, ty + 28], fill=rgb, outline=(210, 210, 214))
            dot_x += 30
        if i >= 4 + 2:  # 概念稿行加个小注
            pass

    # 页眉
    header_h = 96
    canvas = Image.new("RGB", (W, H + header_h), (255, 255, 255))
    canvas.paste(board, (0, header_h))
    d2 = ImageDraw.Draw(canvas)
    f_t = ImageFont.truetype(FONT_PATH, 46)
    f_n = ImageFont.truetype(FONT_PATH, 24)
    d2.text((PAD, 14), "识尘 · 立绘风格锚板  Style Reference", font=f_t, fill=(24, 24, 28))
    d2.text((PAD, 66), "统一画风：日系半厚涂｜纯白底｜全身站姿 2:3｜低饱和灰调 + 每人一处重点色",
            font=f_n, fill=(120, 120, 128))
    d2.line([PAD, header_h - 12, W - PAD, header_h - 12], fill=(225, 225, 228), width=2)

    canvas.save(OUT, "PNG", optimize=True)
    print("OK ->", OUT, canvas.size)


if __name__ == "__main__":
    main()
