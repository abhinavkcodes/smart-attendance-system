import os
import django
import sys
# ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
django.setup()
from django.conf import settings
# allow test client host
settings.ALLOWED_HOSTS = getattr(settings, 'ALLOWED_HOSTS', []) + ['testserver', 'localhost', '127.0.0.1']
from django.test import Client
from students.models import Student

c = Client()
print('GET / ->', c.get('/').status_code)
student = Student.objects.first()
if not student:
    print('No students found in DB. Create one or seed data to test student analytics page.')
    sys.exit(0)
print('Found student pk=', student.pk)
resp = c.get(f'/{student.pk}/attendance/')
print(f'GET /{student.pk}/attendance/ ->', resp.status_code)
resp2 = c.get(f'/charts/attendance/student/{student.pk}.png')
print(f'GET /charts/attendance/student/{student.pk}.png ->', resp2.status_code)
