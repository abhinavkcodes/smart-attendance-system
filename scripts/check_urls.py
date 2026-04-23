import urllib.request

paths = ['/import/','/students/import/']
for p in paths:
    url = 'http://127.0.0.1:8000' + p
    try:
        r = urllib.request.urlopen(url)
        d = r.read(1600).decode('utf-8', errors='replace')
        print('OK', p, 'len', len(d))
        print(d[:800])
    except Exception as e:
        print('ERR', p, repr(e))
