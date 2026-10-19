from pathlib import Path
import re
import markdown
from markdown.extensions.toc import TocExtension

root = Path(__file__).resolve().parents[1]
source_path = root / "教学手册.md"
target_path = Path(__file__).with_name("manual.html")

text = source_path.read_text(encoding="utf-8-sig")
text = text.replace("](diagrams/", "](assets/")
text = re.sub(r"\]\((?!https?://|#|assets/)([^)]+\.md)\)", r"](../\1)", text)
text = text.replace(
    "# 麦轮小车 — 零基础教学手册（阶段 3）",
    "# 麦轮小车 — 零基础教学手册（阶段 3）\n\n[TOC]",
    1,
)


def slugify(value, separator):
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", separator, value, flags=re.UNICODE)
    return value.strip(separator) or "section"


body = markdown.Markdown(
    extensions=[
        "tables",
        "fenced_code",
        "sane_lists",
        TocExtension(slugify=slugify),
    ],
    output_format="html5",
).convert(text)
body = body.replace("<table>", '<div class="table-scroll"><table>')
body = body.replace("</table>", "</table></div>")

template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#090c10">
  <title>教学手册 · 麦轮实验室</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n  <link rel="stylesheet" href="style.css">
</head>
<body class="manual-page" id="manual-top">
  <div class="manual-shell">
    <header class="manual-topbar">
      <a class="brand" href="index.html" aria-label="返回可视化主页">
        <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
        <span class="brand-text"><strong>MECANUM / LAB</strong><small>教学手册</small></span>
      </a>
      <a class="manual-back" href="index.html">← 返回可视化主页</a>
    </header>
    <article class="manual-reader">
__BODY__
      <a class="to-top" href="#manual-top">回到顶部 ↑</a>
    </article>
  </div>
</body>
</html>
"""
target_path.write_text(template.replace("__BODY__", body), encoding="utf-8")
print(f"generated {target_path} ({target_path.stat().st_size} bytes)")

