from pathlib import Path
import base64
import re
import shutil
import zipfile

# 这个脚本把多文件网站打包成两种分享形式：
# 1. 单文件 HTML：CSS、JS、SVG 全部内嵌，适合直接发给别人；
# 2. 完整文件夹 + ZIP：保留原始结构，适合继续修改。
root = Path(__file__).resolve().parent
portable = root / "portable"
portable.mkdir(exist_ok=True)

index_html = (root / "index.html").read_text(encoding="utf-8-sig")
manual_html = (root / "manual.html").read_text(encoding="utf-8-sig")
css = (root / "style.css").read_text(encoding="utf-8-sig")
js = (root / "app.js").read_text(encoding="utf-8-sig")

# 把所有 SVG 转成 data URI，单文件打开时不再依赖 assets 目录。
asset_uris = {}
for path in (root / "assets").glob("*.svg"):
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    asset_uris[path.name] = f"data:image/svg+xml;base64,{encoded}"


def embed_assets(html: str) -> str:
    for name, uri in asset_uris.items():
        html = html.replace(f'src="assets/{name}"', f'src="{uri}"')
        html = html.replace(f'href="assets/{name}"', f'href="{uri}"')
    return html


def inline_css_js(html: str) -> str:
    html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>\n{css}\n</style>')
    html = html.replace('<script src="app.js"></script>', f'<script>\n{js}\n</script>')
    return embed_assets(html)


# 从手册网页中抽取正文，嵌入主站的单文件版本。
manual_match = re.search(r'<article class="manual-reader">(.*?)</article>', manual_html, re.S)
manual_body = manual_match.group(1) if manual_match else "<p>手册正文提取失败。</p>"
manual_body = embed_assets(manual_body)
manual_body = manual_body.replace('href="#manual-top"', 'href="#manual-overlay"')
manual_body = re.sub(r'href="\.\./[^"]+"', 'href="#manual-overlay"', manual_body)

overlay_css = """
/* 单文件分享版：教学手册覆盖层 */
.manual-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  overflow-y: auto;
  padding: 0 max(18px, calc((100vw - 900px) / 2)) 72px;
  background:
    radial-gradient(circle at 78% -8%, rgba(92, 214, 208, .08), transparent 30rem),
    var(--ink);
}
.manual-overlay[hidden] { display: none; }
.manual-overlay-bar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  background: rgba(9, 12, 16, .94);
  backdrop-filter: blur(14px);
}
.manual-overlay-bar strong {
  font-family: var(--mono);
  font-size: .72rem;
  letter-spacing: .1em;
  color: var(--muted);
}
.manual-close {
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--text);
  padding: 7px 12px;
  cursor: pointer;
  font-size: .74rem;
}
.manual-close:hover { border-color: var(--amber); color: var(--amber); }
body.manual-lock { overflow: hidden; }
.manual-inline { margin-top: 18px; }
"""

overlay_html = f"""
<section class="manual-overlay" id="manual-overlay" hidden aria-label="教学手册在线阅读">
  <div class="manual-overlay-bar">
    <strong>FIELD MANUAL / 教学手册</strong>
    <button class="manual-close" id="manual-close" type="button">关闭手册 ×</button>
  </div>
  <article class="manual-reader manual-inline">
{manual_body}
  </article>
</section>
"""

overlay_js = """
/* 单文件分享版：打开/关闭内嵌教学手册 */
(() => {
  const overlay = document.getElementById('manual-overlay');
  const closeButton = document.getElementById('manual-close');
  if (!overlay || !closeButton) return;
  const openManual = (event) => {
    if (event) event.preventDefault();
    overlay.hidden = false;
    document.body.classList.add('manual-lock');
  };
  const closeManual = () => {
    overlay.hidden = true;
    document.body.classList.remove('manual-lock');
  };
  document.querySelectorAll('a[href="manual.html"], [data-open-manual]').forEach((link) => {
    link.addEventListener('click', openManual);
  });
  closeButton.addEventListener('click', closeManual);
  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) closeManual();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !overlay.hidden) closeManual();
  });
})();
"""

single = inline_css_js(index_html)
# 单文件里把外部手册链接改成内嵌覆盖层。
single = single.replace('href="manual.html"', 'href="#manual-overlay" data-open-manual="1"')
single = single.replace('href="../参数手册.md"', 'href="#manual-overlay" data-open-manual="1"')
single = single.replace('href="../Keil使用导航.md"', 'href="#manual-overlay" data-open-manual="1"')
single = single.replace('打开 Markdown', '查看手册内容')
single = single.replace('</head>', f'<style>\n{overlay_css}\n</style>\n</head>')
single = single.replace('</main>', f'{overlay_html}\n      </main>')
single = single.replace('</body>', f'<script>\n{overlay_js}\n</script>\n</body>')
single_path = portable / "麦轮实验室_单文件版.html"
single_path.write_text(single, encoding="utf-8")

# 独立的单文件手册，方便只分享手册。
manual_single = inline_css_js(manual_html)
manual_single = manual_single.replace('href="index.html"', 'href="#manual-top"')
manual_single = re.sub(r'href="\.\./[^"]+"', 'href="#manual-top"', manual_single)
manual_single_path = portable / "教学手册_单文件版.html"
manual_single_path.write_text(manual_single, encoding="utf-8")

# 完整分享文件夹：保留原结构，方便继续编辑。
share_dir = portable / "麦轮实验室_离线版"
share_dir.mkdir(exist_ok=True)
(share_dir / "assets").mkdir(exist_ok=True)
for name in ["index.html", "manual.html", "style.css", "app.js"]:
    shutil.copy2(root / name, share_dir / name)
for path in (root / "assets").glob("*"):
    if path.is_file():
        shutil.copy2(path, share_dir / "assets" / path.name)
for name in ["参数手册.md", "Keil使用导航.md", "教学手册.md"]:
    source = root.parent / name
    if source.exists():
        shutil.copy2(source, share_dir / name)
shutil.copy2(single_path, share_dir / single_path.name)
shutil.copy2(manual_single_path, share_dir / manual_single_path.name)

readme = """麦轮实验室 · 离线分享包
================================

为什么直接打开 ZIP 里的 index.html 会没有背景和 UI？
- ZIP 预览窗口可能只解压了 index.html；
- 浏览器找不到同目录的 style.css、app.js 和 assets/，于是只剩裸 HTML。

正确打开方式（推荐）
--------------------
1. 先把整个压缩包解压到普通文件夹；
2. 双击文件夹里的 index.html；
3. 不要直接在 ZIP 预览窗口里双击。

最省事的分享方式
----------------
直接发送“麦轮实验室_单文件版.html”。
这个文件已经内嵌 CSS、JS、SVG 和教学手册，单独一个文件即可打开。

文件说明
--------
- index.html                  多文件版入口
- manual.html                 多文件版教学手册
- 麦轮实验室_单文件版.html    推荐分享的单文件版
- 教学手册_单文件版.html      独立单文件教学手册
- style.css / app.js / assets 多文件版依赖，不能单独删除
- 参数手册.md / Keil使用导航.md / 教学手册.md 原始文档

注意
----
- 网站不需要联网，也不会上传数据；
- 网站不连接真实串口，是教学、标定计算和协议演示工具；
- 如果浏览器仍显示旧样式，按 Ctrl+F5 强制刷新。
"""
(share_dir / "打开说明.txt").write_text(readme, encoding="utf-8")

# 打包 ZIP，根目录保留一个易识别的文件夹。
zip_path = portable / "麦轮实验室_离线分享包.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in share_dir.rglob("*"):
        if path.is_file():
            archive.write(path, Path(share_dir.name) / path.relative_to(share_dir))

print(f"单文件主站: {single_path} ({single_path.stat().st_size} bytes)")
print(f"单文件手册: {manual_single_path} ({manual_single_path.stat().st_size} bytes)")
print(f"完整分享包: {zip_path} ({zip_path.stat().st_size} bytes)")

