from pathlib import Path
p=Path('PC_上位机/ui/main_window.py')
lines=p.read_text(encoding='utf-8-sig').splitlines()
for i,l in enumerate(lines):
    if l.strip() == 'return scroll                                      # 返回控制页':
        lines.insert(i, '        scroll.setWidget(page)                             # 设置滚动内容')
        break
p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('inserted')
