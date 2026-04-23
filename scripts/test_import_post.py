import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print('requests not installed')
    sys.exit(2)

base='http://127.0.0.1:8000'
import_url=base+'/students/import/'

s=requests.Session()
print('GET', import_url)
r=s.get(import_url, timeout=10)
print('GET status', r.status_code)
# extract csrf token
m=re.search(r'name="csrfmiddlewaretoken" value="([A-Za-z0-9\-]+)"', r.text)
if not m:
    print('csrf token not found')
    print(r.text[:500])
    sys.exit(1)
csrf=m.group(1)
print('CSRF', csrf)

# open sample csv
csv_path=Path(r'C:/Users/imabh/OneDrive/Desktop/FDS4/students/static/students/csv/sample_students.csv')
if not csv_path.exists():
    print('sample CSV missing', csv_path)
    sys.exit(1)

files={'file': ('sample_students.csv', open(csv_path,'rb'), 'text/csv')}
data={'csrfmiddlewaretoken': csrf}
# include referer header
headers={'Referer': import_url}
print('POSTing file...')
pr=s.post(import_url, files=files, data=data, headers=headers, timeout=30)
print('POST status', pr.status_code)
print(pr.text[:1000])
