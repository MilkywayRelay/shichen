# -*- coding: utf-8 -*-
"""从识尘设定库抽取 16 份人设的关键字段，生成站点侧速查表 docs/角色设定速查.md。
用途：避免每次改动都去翻 obsidian 原档。原档仍为唯一权威源。"""
import re, glob, os, io

SRC = 'E:/obsidian-vault/DarkBook/10-Projects/01-Current/识尘/角色形象'
INST = 'E:/obsidian-vault/DarkBook/10-Projects/01-Current/识尘/世界体系/机构与人物介绍（更新版）.md'

FIELDS = ['性别', '年龄', '身份', '身高与体型', '整体印象', '肤质', '五官',
          '发型与发色', '脸型', '面部标记', '特殊体征', '日常装束',
          '标志性配饰', '鞋履类型', '站姿习惯']

# 名册顺序（与 js/app.js ROSTER 一致）
ORDER = ['ISFJ','ENFP','ENTJ','ISTP','ESTJ','ESFJ','INFJ','ENFJ',
         'INTP','ISFP','ISTJ','ESTP','INTJ','ENTP','INFP','ESFP']

def grab(text, field):
    m = re.search(r'[·•]\s*' + re.escape(field) + r'(?:／[^：:]+)?[：:]\s*(.+)', text)
    return m.group(1).strip() if m else ''

def draft_count(text):
    n = 0
    for ln in text.splitlines():
        if '【待定】' in ln and not re.search(r'标注|保持|其余标注|留待补全|【说明】', ln):
            n += ln.count('【待定】')
    return n

rows = []
for p in glob.glob(os.path.join(SRC, '*.md')):
    code = os.path.splitext(os.path.basename(p))[0]
    t = open(p, encoding='utf-8').read()
    rows.append((code, t))

by = {c: t for c, t in rows}

out = io.StringIO()
w = out.write
w('# 识尘企划 · 角色设定速查\n\n')
w('> **本文件是检索用的派生物，不是权威源。**\n')
w('> 权威源：`识尘/角色形象/<代号>.md`（人设）与 `识尘/世界体系/机构与人物介绍（更新版）.md`（机构与人物）。\n')
w('> 改动请改原档，然后重跑 `tools/extract_profiles.py` 重新生成本表。\n\n')
w(f'共 {len(ORDER)} 名在册人员。`【待定】` 计数用于名册灰卡判定（≥2 处＝档案未定稿）。\n\n')
w('---\n\n')
w('## 一览\n\n')
w('| 代号 | 性别 | 年龄 | 身份 | 待定项 | 原画 |\n|---|---|---|---|---|---|\n')
have_art = {'ISFJ','ENFP','ENTJ','ISTP'}
for c in ORDER:
    t = by.get(c, '')
    n = draft_count(t)
    art = '有' if c in have_art else '—'
    w(f'| {c} | {grab(t,"性别")} | {grab(t,"年龄")[:14]} | {grab(t,"身份")[:26]} | '
      f'{"●"*min(n,6)} {n} | {art} |\n')
w('\n---\n\n')

for c in ORDER:
    t = by.get(c, '')
    if not t:
        continue
    w(f'## {c}\n\n')
    for f in FIELDS:
        v = grab(t, f)
        if v:
            w(f'- **{f}**：{v}\n')
    w(f'- *来源*：`角色形象/{c}.md`\n\n')

open('docs/角色设定速查.md', 'w', encoding='utf-8').write(out.getvalue())
print('written docs/角色设定速查.md', len(out.getvalue()), 'chars')
