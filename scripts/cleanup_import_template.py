import io
from pathlib import Path
p = Path(r"C:/Users/imabh/OneDrive/Desktop/FDS4/students/templates/students/import_csv.html")
text = p.read_text(encoding='utf-8-sig')
lines = text.splitlines()
# Remove leading/trailing code fence lines that are exactly ``` or ```html
if lines and lines[0].strip().startswith('```'):
    lines = lines[1:]
if lines and lines[-1].strip().startswith('```'):
    lines = lines[:-1]
new_text = '\n'.join(lines)
# Ensure file ends with a newline
if not new_text.endswith('\n'):
    new_text += '\n'
p.write_text(new_text, encoding='utf-8')
print('cleaned', p)
