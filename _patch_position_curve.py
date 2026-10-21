from pathlib import Path
p=Path('PC_上位机/ui/main_window.py')
lines=p.read_text(encoding='utf-8-sig').splitlines()
for i,l in enumerate(lines):
    if 'if hasattr(self, "pid_curve_panel")' in l and '控制页曲线' in l:
        lines.insert(i, '                if hasattr(self, "curve_panel"):            # 主曲线页也显示位置')
        lines.insert(i+1, '                    self.curve_panel.update_position(target_mm, actual_mm, error_mm)   # 更新主曲线位置')
        break
p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('inserted position sync')
