import os
import sys

# Ensure project path
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
from django.urls import reverse

django.setup()

names = [
    'list', 'add', 'import_csv', 'export_csv', 'analytics',
    'attendance', 'attendance_debug', 'attendance_export',
    'gpa_hist', 'enrollment_trend', 'cgpa_analyzer', 'dept_cgpa_heatmap',
    'detail', 'edit', 'delete',
]

print('Attempting to reverse students:... names')
for n in names:
    try:
        if n in ('detail', 'edit', 'delete'):
            url = reverse(f'students:{n}', args=[1])
        else:
            url = reverse(f'students:{n}')
        print(f'OK  students:{n} ->', url)
    except Exception as e:
        print(f'ERR students:{n} ->', type(e).__name__, str(e))

# Also try admin analytics view name if used
from django.urls import reverse as r
try:
    print('Admin analytics reverse:', r('admin:analytics'))
except Exception as e:
    print('Admin analytics ERR ->', type(e).__name__, str(e))

# Also write a simple output file for easier inspection
out_path = os.path.join(BASE, 'tools', 'check_urls_out.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('Results for students URL reverse\n')
    for n in names:
        try:
            if n in ('detail', 'edit', 'delete'):
                url = reverse(f'students:{n}', args=[1])
            else:
                url = reverse(f'students:{n}')
            f.write(f'OK students:{n} -> {url}\n')
        except Exception as e:
            f.write(f'ERR students:{n} -> {type(e).__name__}: {e}\n')
    try:
        f.write('Admin analytics reverse: ' + r('admin:analytics') + '\n')
    except Exception as e:
        f.write('Admin analytics ERR -> ' + type(e).__name__.__name__ + ': ' + str(e) + '\n')
print('\nWrote results to', out_path)
