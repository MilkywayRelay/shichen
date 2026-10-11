# 识尘 · Shichen

原创世界观企划「识尘」的官方网站。纯静态站点，无构建步骤、无依赖。

> 人类认知的极限，是另一种文明的起点。

## 本地预览

站点用了 `fetch`/模块等需要 HTTP 协议的能力，**不能直接双击 index.html**，需起一个本地服务：

```bash
python -m http.server 8712 --bind 127.0.0.1
# 打开 http://127.0.0.1:8712/index.html
```

## 目录结构

```
index.html            单页骨架，7 个板块
css/style.css         全部样式（CSS 变量集中在 :root）
js/app.js             全部交互与数据（角色数据在 CHARS 常量里）
assets/char/          在用的角色立绘定稿（ISFJ/ENFP/ENTJ/ISTP/Mana）
assets/img/           场景图（hero / dustsphere / fortress）
docs/                 立绘风格定稿基准（Style Bible）、角色设定速查、风格锚板
tools/                图像处理 / 自检脚本（Python，需 cv2、PIL、numpy）
```

**未纳入版本控制**（见 `.gitignore`）：`assets/char/_gen/`（图生图迭代稿 156MB）、
`_shots/`（自检截图 209MB）、`_deliver/`（交付对照图 114MB）、`_anchor/`（画风锚素材）。
这些是过程资产，本地保留即可；仓库只放站点本体与文档，克隆后约 15MB。

## 部署到 GitHub Pages

仓库已带 `.github/workflows/pages.yml`：推送到 `main` 即自动构建发布。

1. 在 GitHub 新建空仓库（建议名 `shichen`），**不要**勾选初始化 README / .gitignore / license
2. 关联并推送：

   ```bash
   git remote add origin git@github.com:MilkywayRelay/shichen.git
   git push -u origin main
   ```

   > 若没配 SSH key，改用 HTTPS：
   > `git remote add origin https://github.com/MilkywayRelay/shichen.git`
   > 密码处填 **Personal Access Token**（Settings → Developer settings →
   > Personal access tokens → Tokens(classic)，勾选 `repo`），不是登录密码。

3. 仓库 **Settings → Pages → Source** 选 **GitHub Actions**
4. 稍等片刻，Actions 跑完即给出 `https://milkywayrelay.github.io/shichen/`

也可以 `Actions → Deploy to GitHub Pages → Run workflow` 手动触发。

## 改资源记得 bump 版本号

站点是纯静态且会被 CDN / 浏览器强缓存。**换过图片或改过 CSS、JS 之后，必须同步改 `index.html` 里的 `?v=`**，否则线上仍会读旧文件：

```html
<link rel="stylesheet" href="css/style.css?v=21">
<script src="js/app.js?v=14"></script>
```

角色立绘的版本号写在 `js/app.js` 的 `CHARS[].img` 里（如 `assets/char/entj.png?v=5`）。

## 角色立绘口径

- 人物形象的**唯一权威**在 Obsidian 库 `10-Projects/01-Current/识尘/角色形象/`（`原画/` = 画师原作）
- 站点在用的是**立绘定稿**（已同步备份到库的 `角色形象/立绘定稿/`）
- 出新角色或改立绘前，**先读 `docs/立绘风格定稿基准.md`**：画风锚点、锚色表、
  角色锁定卡、生图 prompt 模板、避坑清单都在里面，能省掉大量返工
- 铁律：**人物不纯文生图**（会把造型归一化），只能拿已有立绘当参考图做图生图
