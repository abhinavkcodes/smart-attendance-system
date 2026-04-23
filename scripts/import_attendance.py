#!/usr/bin/env python3
"""
Simple Django-aware script to import attendance from a CSV.
CSV must have columns: enrollment_no,date,status,notes (notes optional)
Date should be YYYY-MM-DD.
Run from project root:
    python scripts/import_attendance.py path/to/attendance.csv

This uses the Django ORM so it will match students by enrollment_no and upsert Attendance rows.
"""
import os
import sys
import csv
from datetime import datetime

# adjust this if your project settings module is different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from students.models import Student, Attendance


def usage():
    print('Usage: python scripts/import_attendance.py path/to/file.csv')
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    path = sys.argv[1]
    if not os.path.exists(path):
        print('File not found:', path)
        sys.exit(1)

    created = 0
    updated = 0
    skipped = 0

    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=1):
            enr = (row.get('enrollment_no') or row.get('enrollment') or row.get('enrol') or '').strip()
            date_s = (row.get('date') or row.get('attendance_date') or '').strip()
            status = (row.get('status') or '').strip().lower()
            notes = row.get('notes') or ''

            if not enr or not date_s or not status:
                print(f'Row {i}: missing required field, skipping')
                skipped += 1
                continue
            try:
                date = datetime.strptime(date_s, '%Y-%m-%d').date()
            except Exception:
                print(f'Row {i}: invalid date "{date_s}", expected YYYY-MM-DD; skipping')
                skipped += 1
                continue
            try:
                student = Student.objects.get(enrollment_no=enr)
            except Student.DoesNotExist:
                print(f'Row {i}: student with enrollment_no {enr} not found; skipping')
                skipped += 1
                continue

            obj, created_flag = Attendance.objects.update_or_create(
                student=student, date=date,
                defaults={'status': status, 'notes': notes}
            )
            if created_flag:
                created += 1
            else:
                updated += 1

    print(f'Done. created={created}, updated={updated}, skipped={skipped}')
