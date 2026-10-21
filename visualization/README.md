> 2026-10-21：普通手动、固定路线、旋转不使用 PID，也不使用缓起/缓停；PID 仅在控制与测试页使用。网站中的历史手册段落已标记为旧版本。

# 麦轮实验室 · 离线可视化网站

这是阶段 4 的可视化教学网站，使用纯静态 HTML/CSS/JS，不依赖 CDN、Node 或后端服务。

## 打开方式

直接双击：

`visualization\index.html`

也可以在本目录运行一个本地静态服务器：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

然后打开 `http://127.0.0.1:8765/`。

`file://` 方式也能打开；个别浏览器可能限制 `localStorage`，此时标定输入不会被保存，但所有计算和交互仍然可用。

## 页面

- `index.html`：总览、架构、代码地图、参数中心、标定向导、麦轮运动学、PID 模拟、协议实验室、故障排查；
- `manual.html`：由 `..\教学手册.md` 生成的教学手册在线阅读版；
- `assets/`：从 `..\diagrams/` 复制来的 SVG 示意图；
- `build_manual.py`：重新生成 `manual.html` 的脚本；
- `style.css`：优雅黑视觉系统与手机响应式布局；
- `app.js`：所有交互、计算和可视化逻辑。

## 修改内容

- 参数表、代码地图、故障排查：编辑 `app.js` 顶部的数据数组；
- 颜色、字号、间距：编辑 `style.css` 顶部的 `:root` 变量；
- 教学手册正文：编辑 `..\教学手册.md`，然后运行：

```powershell
python visualization\build_manual.py
```

> 重新生成手册需要本机安装 Python 的 `markdown` 包。  
> 本网站不连接真实串口，也不会向网络发送数据；它是教学和标定计算工具，不是上位机替代品。


## 测试截图

screenshots/ 保存了桌面、手机和手册阅读的浏览器冒烟测试截图，不是网站运行所必需的文件。



## 分享给别人

- 单文件主站：`portable/麦轮实验室_单文件版.html`；
- 单文件手册：`portable/教学手册_单文件版.html`；
- 完整分享包：`portable/麦轮实验室_离线分享包.zip`。

原来的 `manual.html` 依赖 `style.css` 和 `assets/`，如果只发这一个 HTML，收到的人会看不到背景和图片；分享时请用单文件版或完整 ZIP。

