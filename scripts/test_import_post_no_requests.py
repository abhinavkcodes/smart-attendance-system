import re, sys, urllib.request, urllib.error, http.cookiejar
from pathlib import Path

def encode_multipart_formdata(fields, files):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    crlf = '\r\n'
    lines = []
    for (key, value) in fields.items():
        lines.append('--' + boundary)
        lines.append(f'Content-Disposition: form-data; name="{key}"')
        lines.append('')
        lines.append(value)
    for (key, filename, value, content_type) in files:
        lines.append('--' + boundary)
        lines.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"')
        lines.append(f'Content-Type: {content_type}')
        lines.append('')
        lines.append(value)
    lines.append('--' + boundary + '--')
    lines.append('')
    body = crlf.join(line if isinstance(line, str) else line.decode('utf-8') for line in lines)
    return body.encode('utf-8'), f'multipart/form-data; boundary={boundary}'

base='http://127.0.0.1:8000'
import_url=base+'/students/import/'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
print('GET', import_url)
resp = opener.open(import_url)
html = resp.read().decode('utf-8', errors='replace')
print('GET status', resp.getcode())
# extract csrf token
m=re.search(r'name="csrfmiddlewaretoken" value="([A-Za-z0-9\-]+)"', html)
if not m:
    print('csrf token not found')
    sys.exit(1)
csrf=m.group(1)
print('CSRF', csrf)

# read sample csv
csv_path=Path(r'C:/Users/imabh/OneDrive/Desktop/FDS4/students/static/students/csv/sample_students.csv')
if not csv_path.exists():
    print('sample CSV missing', csv_path)
    sys.exit(1)
csv_bytes = csv_path.read_bytes()

fields = {'csrfmiddlewaretoken': csrf}
files = [('file', 'sample_students.csv', csv_bytes.decode('utf-8'), 'text/csv')]
body, content_type = encode_multipart_formdata(fields, files)
req = urllib.request.Request(import_url, data=body, method='POST')
req.add_header('Content-Type', content_type)
req.add_header('Referer', import_url)
print('POSTing...')
try:
    r2 = opener.open(req, timeout=30)
    print('POST status', r2.getcode())
    out = r2.read().decode('utf-8', errors='replace')
    print(out[:1000])
except urllib.error.HTTPError as e:
    print('HTTPError', e.code)
    print(e.read().decode('utf-8', errors='replace')[:2000])
    sys.exit(1)
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
