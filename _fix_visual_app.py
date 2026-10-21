from pathlib import Path
p=Path('visualization/app.js')
lines=p.read_text(encoding='utf-8-sig').splitlines()
for i,l in enumerate(lines):
    if 'decoded = `目标距离=' in l:
        lines.insert(i+1, '    }')
        break
p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('brace inserted')
