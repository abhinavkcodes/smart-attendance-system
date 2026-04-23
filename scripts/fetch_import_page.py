import urllib.request, urllib.error, sys
url='http://127.0.0.1:8000/students/import/'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        data=r.read()
        print('STATUS', r.status)
        print(data.decode('utf-8', errors='replace'))
except urllib.error.HTTPError as e:
    print('HTTP ERROR', e.code)
    try:
        body = e.read().decode('utf-8', errors='replace')
        # Save full debug page for inspection
        with open(r"C:/Users/imabh/OneDrive/Desktop/FDS4/scripts/import_error.html", 'w', encoding='utf-8') as f:
            f.write(body)
        print('WROTE scripts/import_error.html')
        print(body[:2000])
    except Exception as e2:
        print('could not read body', e2)
    sys.exit(1)
except Exception as e:
    print('ERROR', repr(e))
    sys.exit(1)
