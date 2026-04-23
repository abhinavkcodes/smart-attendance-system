import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from students import views

rf = RequestFactory()
req = rf.post('/students/attendance/', {'status_1': 'present'})
req.session = SessionStore()
req._messages = FallbackStorage(req)

try:
    resp = views.attendance_page(req)
    print('RESPONSE:', type(resp), getattr(resp, 'status_code', None))
except Exception:
    traceback.print_exc()
