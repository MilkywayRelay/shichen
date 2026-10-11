"""Mana 用户图 -> 透明底（v3）

在 v2 基础上修复两个问题：
  1. 发丝围成的封闭空隙（不与画面边界连通的暖米色区域）此前漏抠
     —— 新增「全图孔洞填充」：cand 中不与边界连通的孤立连通域，
        只要颜色≈背景色且尺寸不大，一律判为背景。
  2. 底部改为更长的柔和渐隐（smoothstep），避免裙摆末端出现生硬截断/残渣。

背景米色 BG≈(252,247,235)：R-B≈18、蓝通道≈235；
光环淡金 B≈211-224、白袍 B≈255 且 R≈B —— 用蓝通道 + 暖色同时约束可区分。

用法:
    python tools/mana_user_prep2.py                # 默认全流程
    python tools/mana_user_prep2.py <src> <dst_out_full> <dst_final>
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/char/mana_user/user_pick.jpg"
DST_FULL = sys.argv[2] if len(sys.argv) > 2 else "assets/char/mana_user/mana_cut2.png"
DST_FINAL = sys.argv[3] if len(sys.argv) > 3 else "assets/char/mana.png"

BG = np.array([252.4, 246.6, 234.6], dtype=np.float32)
FADE_START = 0.870      # 底部渐隐起点（占全高比例）
FADE_END = 0.992        # 完全透明处

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.float32)
h, w = a.shape[:2]
N = h * w
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = 0.299 * R + 0.587 * G + 0.114 * B
print("src", im.size)

# ---------- 1) 背景候选 ----------
cand = ((R - B) > 11) & (lum > 233) & (B > 229)
print("cand %.2f%%" % (100 * cand.mean()))


def bfs_from_border(mask):
    """mask 中与画面四边连通的区域（4 邻接）"""
    out = np.zeros(N, dtype=bool)
    flat = mask.reshape(-1)
    q = []
    for x in range(w):
        for y in (0, h - 1):
            j = y * w + x
            if flat[j] and not out[j]:
                out[j] = True
                q.append(j)
    for y in range(h):
        for x in (0, w - 1):
            j = y * w + x
            if flat[j] and not out[j]:
                out[j] = True
                q.append(j)
    head = 0
    while head < len(q):
        i = q[head]
        head += 1
        y, x = divmod(i, w)
        if y > 0 and flat[i - w] and not out[i - w]:
            out[i - w] = True; q.append(i - w)
        if y < h - 1 and flat[i + w] and not out[i + w]:
            out[i + w] = True; q.append(i + w)
        if x > 0 and flat[i - 1] and not out[i - 1]:
            out[i - 1] = True; q.append(i - 1)
        if x < w - 1 and flat[i + 1] and not out[i + 1]:
            out[i + 1] = True; q.append(i + 1)
    return out.reshape(h, w)


def label(mask, min_size=8, max_bbox=280):
    """连通域标记；返回 [(mask_bool, size)]，过滤过小/过大"""
    lab = np.zeros(N, dtype=np.int32)
    flat = mask.reshape(-1)
    res = []
    cur = 0
    order = np.flatnonzero(flat)
    for s in order:
        if lab[s] != 0:
            continue
        cur += 1
        lab[s] = cur
        q = [int(s)]
        head = 0
        px = []
        while head < len(q):
            i = q[head]
            head += 1
            px.append(i)
            y, x = divmod(i, w)
            for j in (
                i - w if y > 0 else -1,
                i + w if y < h - 1 else -1,
                i - 1 if x > 0 else -1,
                i + 1 if x < w - 1 else -1,
            ):
                if j >= 0 and flat[j] and lab[j] == 0:
                    lab[j] = cur
                    q.append(j)
        if len(px) < min_size:
            continue
        idx = np.array(px)
        yy, xx = np.divmod(idx, w)
        if (xx.max() - xx.min()) > max_bbox or (yy.max() - yy.min()) > max_bbox:
            continue
        m = np.zeros(N, dtype=bool)
        m[idx] = True
        res.append((m.reshape(h, w), len(px)))
    return res


# ---------- 2) 边界连通 = 背景 ----------
bg = bfs_from_border(cand)
print("bg(after border flood) %.2f%%" % (100 * bg.mean()))

# ---------- 3a) 头顶补丁：光环圈内的背景被环线隔断，泛洪到不了 ----------
diff = np.abs(a - BG).max(axis=2)
patch = np.zeros_like(bg)
patch[0:int(h * 0.215), int(w * 0.25):int(w * 0.75)] = True
patched = int((cand & patch & ~bg).sum())
bg |= (cand & patch)
print("halo patch: +%d px -> bg %.2f%%" % (patched, 100 * bg.mean()))

# ---------- 3b) 孔洞填充：发丝围成的封闭空隙 ----------
# 严格判据：颜色必须与背景几乎一致（JPEG 噪点范围内）+ 面积很小
# —— 白袍的暖白高光虽然也偏暖，但与背景有色差且成片，不会被误删
holes = cand & ~bg
filled = 0
cnt_hole = 0

# 实测结论（诊断可视化）：
#   真正的发丝/指缝镂空，颜色与背景几乎一致（diff≈3、蓝通道≈235），面积可达数千像素；
#   而裙摆处的米色褶皱阴影颜色同样接近背景 —— 单靠颜色无法区分二者。
#   但发丝镂空只出现在画面上半部的碎发区，因此用纵向范围把它们隔离开。
HOLE_Y_LIMIT = 0.62

# 前景"厚度"图：把已确认背景反复膨胀 12px 后仍覆盖不到的前景 = 粗大的实体
# （躯干、袍面大块）；覆盖面内 = 细结构（发丝）。碎发镂空的四周一定是细结构。
_cur = (bg.astype(np.uint8)) * 255
for _ in range(12):
    _cur = np.asarray(Image.fromarray(_cur).filter(ImageFilter.MaxFilter(3)))
thick = (~bg) & (_cur == 0)
print("thick-foreground %.2f%%" % (100 * thick.mean()))

dbg = []
for m, size in label(holes, min_size=10, max_bbox=10 ** 9):
    ys_, xs_ = np.where(m)
    if ys_.mean() > h * HOLE_Y_LIMIT:
        continue                    # 裙摆区：米色褶皱与背景同色，一律不动
    dm = diff[m]
    if dm.mean() > 6.0 or np.percentile(dm, 90) > 10.0:
        continue                    # 与背景有色差 -> 是布料
    if B[m].mean() > 242:
        continue                    # 蓝通道明显高于背景 -> 袍面高光，保留
    pad = 5
    y0b, y1b = max(0, ys_.min() - pad), min(h, ys_.max() + pad + 1)
    x0b, x1b = max(0, xs_.min() - pad), min(w, xs_.max() + pad + 1)
    tf = float(thick[y0b:y1b, x0b:x1b].mean())
    dbg.append((size, round(float(dm.mean()), 1), round(float(B[m].mean()), 1), round(tf, 2),
                int(xs_.mean()), int(ys_.mean())))
    bg |= m
    filled += size
    cnt_hole += 1
dbg.sort(key=lambda t: -t[0])
print("hole candidates:", len(dbg))
for t in dbg[:30]:
    print("   size=%6d diff=%4.1f B=%5.1f thick=%.2f  at(%d,%d)" % t)
print("hole-fill: %d blobs, %d px -> bg %.2f%%" % (cnt_hole, filled, 100 * bg.mean()))

# ---------- 4) 孤立前景小岛（与主体不相连、颜色≈背景的碎片）----------
island = 0
for m, size in label(~bg, min_size=30, max_bbox=10 ** 9):
    if size >= 4000:
        continue
    if (diff[m] < 15).mean() > 0.55:
        bg |= m
        island += size
print("island-removed %d px -> bg %.2f%%" % (island, 100 * bg.mean()))

# ---------- 5) alpha ----------
alpha = np.where(bg, 0.0, 1.0).astype(np.float32)
am = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
alpha = np.asarray(am).astype(np.float32) / 255.0

# ---------- 6) 底部柔和渐隐（smoothstep）----------
y0, y1 = int(h * FADE_START), int(h * FADE_END)
yy = np.arange(h, dtype=np.float32)
t = np.clip((yy - y0) / max(1, (y1 - y0)), 0.0, 1.0)
t = t * t * (3 - 2 * t)                      # smoothstep
ramp = np.where(yy < y0, 1.0, 1.0 - t)
alpha *= ramp[:, None]
print("bottom fade: %d -> %d (rows %.0f%%-%.0f%%)" % (y0, y1, 100 * FADE_START, 100 * FADE_END))

# ---------- 7) 反预乘 ----------
al = alpha[..., None]
gain = np.minimum(1.0 / np.clip(al, 1e-3, 1.0), 4.0)
rgb = BG + (a - BG) * gain
rgb = np.clip(rgb, 0, 255)

# ---------- 8) 色度平滑 ----------
tmp = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("YCbCr")
y_, cb_, cr_ = tmp.split()
cb_ = cb_.filter(ImageFilter.GaussianBlur(0.7))
cr_ = cr_.filter(ImageFilter.GaussianBlur(0.7))
rgb = np.asarray(Image.merge("YCbCr", (y_, cb_, cr_)).convert("RGB")).astype(np.float32)

full = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
full.save(DST_FULL)
print("saved full", DST_FULL, full.size)

# ---------- 9) 缩放到站点尺寸 1024x1536 + 内部轻度锐化 ----------
TW, TH = 1024, 1536
small = full.resize((TW, TH), Image.LANCZOS)
sm_rgb = small.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.3, percent=45, threshold=4))
sa = np.asarray(small)
al_s = sa[..., 3]
res = np.asarray(small.convert("RGB")).copy()
solid = al_s > 250
res[solid] = np.asarray(sm_rgb)[solid]
Image.fromarray(np.dstack([res, al_s]).astype(np.uint8), "RGBA").save(DST_FINAL)
print("saved final", DST_FINAL, (TW, TH))
