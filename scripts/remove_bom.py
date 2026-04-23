p = r'c:\Users\imabh\OneDrive\Desktop\FDS4\students\templates\students\import_csv.html'
with open(p, 'r', encoding='utf-8-sig') as f:
    s = f.read()
with open(p, 'w', encoding='utf-8') as f:
    f.write(s)
print('wrote', p)