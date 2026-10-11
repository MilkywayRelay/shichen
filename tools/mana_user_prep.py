"""Mana 用户选定图 -> 透明底（v2）
背景米色 B≈234，光环淡金 B≈211-224，白袍 B≈255。
判据：暖色(R-B>11) + 高亮 + 蓝通道偏高(B>229) + 与画面边界连通  => 背景
再对"被包围的孤立背景孔洞"（光环圈内）做填充。
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/char/mana_user/user_pick.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "assets/char/mana_user/mana_cut.png"

im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.float32)
h, w = a.shape[:2]
N = h * w
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = 0.299 * R + 0.587 * G + 0.114 * B
BG = np.array([252.4, 246.6, 234.6], dtype=np.float32)


def bfs(mask):
    """返回与画面四边连通的 True 区域"""
    out = np.zeros(N, dtype=bool)
    flat = mask.reshape(-1)
    q = []
    for x in range(w):
        for y in (0, h - 1):
            j = y * w + x
            if flat[j] and not out[j]:
                out[j] = True; q.append(j)
    for y in range(h):
        for x in (0, w - 1):
            j = y * w + x
            if flat[j] and not out[j]:
                out[j] = True; q.append(j)
    head = 0
    while head < len(q):
        i = q[head]; head += 1
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


def components(mask):
    """连通域标记（4 邻接），返回 label 数组"""
    lab = np.zeros(N, dtype=np.int32)
    flat = mask.reshape(-1)
    cur = 0
    for s in range(N):
        if flat[s] and lab[s] == 0:
            cur += 1
            lab[s] = cur
            q = [s]; head = 0
            while head < len(q):
                i = q[head]; head += 1
                y, x = divmod(i, w)
                if y > 0 and flat[i - w] and lab[i - w] == 0:
                    lab[i - w] = cur; q.append(i - w)
                if y < h - 1 and flat[i + w] and lab[i + w] == 0:
                    lab[i + w] = cur; q.append(i + w)
                if x > 0 and flat[i - 1] and lab[i - 1] == 0:
                    lab[i - 1] = cur; q.append(i - 1)
                if x < w - 1 and flat[i + 1] and lab[i + 1] == 0:
                    lab[i + 1] = cur; q.append(i + 1)
    return lab.reshape(h, w), cur


# 1) 背景候选
cand = ((R - B) > 11) & (lum > 233) & (B > 229)
print("cand %.2f%%" % (100 * cand.mean()))

# 2) 与边界连通
bg = bfs(cand)
print("bg(after flood) %.2f%%" % (100 * bg.mean()))

# 3) 头顶补丁：光环圈内的背景与外部被环线隔开，
#    该区域只有 背景/光环/头发，可直接按颜色判定（不做连通性限制）
y0, y1 = 0, int(h * 0.215)
x0, x1 = int(w * 0.25), int(w * 0.75)
patch = np.zeros_like(bg)
patch[y0:y1, x0:x1] = True
bg |= (cand & patch)
print("bg(after halo patch) %.2f%%" % (100 * bg.mean()))

# 4) 清理：与人物主体不相连、且颜色≈背景的孤立小岛 -> 也算背景
diff = np.abs(a - BG).max(axis=2)
lab, n = components(~bg)
print("fg components:", n)
removed = 0
for k in range(1, n + 1):
    m = lab == k
    cnt = int(m.sum())
    if cnt < 4000 and (diff[m] < 15).mean() > 0.55:
        bg |= m
        removed += cnt
print("island-removed px", removed, " -> bg %.2f%%" % (100 * bg.mean()))

# 4) alpha 软边
alpha = np.where(bg, 0.0, 1.0).astype(np.float32)
am = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
alpha = np.asarray(am).astype(np.float32) / 255.0

# 5) 底部渐隐
fade_h = int(h * 0.07)
ramp = np.linspace(1.0, 0.0, fade_h).astype(np.float32)[:, None]
alpha[h - fade_h:, :] *= ramp

# 6) 反预乘（限制放大倍数，避免低 alpha 区爆出彩噪）
al = alpha[..., None]
gain = np.minimum(1.0 / np.clip(al, 1e-3, 1.0), 4.0)
rgb = BG + (a - BG) * gain
rgb = np.clip(rgb, 0, 255)

# 7) 色度平滑：压掉反预乘放大的彩色噪点（亮度不动，结构不糊）
tmp = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("YCbCr")
y_, cb_, cr_ = tmp.split()
cb_ = cb_.filter(ImageFilter.GaussianBlur(0.7))
cr_ = cr_.filter(ImageFilter.GaussianBlur(0.7))
rgb = np.asarray(Image.merge("YCbCr", (y_, cb_, cr_)).convert("RGB")).astype(np.float32)

Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA").save(DST)
print("saved", DST)
