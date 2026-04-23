#!/usr/bin/env python3
r"""
Import aggregated attendance CSV into per-day Attendance rows.
CSV must contain columns (case-insensitive):
 - enrollment_no
 - Total_Sessions (int)
 - Present_Rate (e.g. "89%") OR Present_Count (optional)
 - Late (int) -- number of late sessions
 - Absent (int) -- number of absent sessions
 - notes (optional)

Behavior:
 - For each row, match Student by enrollment_no. If not found, skip and report.
 - Compute present_count = Total_Sessions - Late - Absent (if Present_Count not provided).
 - Create Total_Sessions Attendance rows for consecutive past days ending today.
 - Distribute statuses (present/late/absent) across those dates in a reproducible shuffled order.
 - Use update_or_create to avoid duplicate date entries (it will overwrite status/notes for same date).

Warning: this synthesizes day-level attendance from aggregated counts. Keep a DB backup before running in production.

Run from project root:
  python scripts/import_aggregated_attendance.py "C:\Users\imabh\OneDrive\Desktop\srm_ktr_students idk.csv"

"""
import os
import sys
import csv
from datetime import datetime, timedelta
import random

# adjust this if your project settings module is different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
# ensure project root is on sys.path so imports like 'myproject' work when script is run
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
django.setup()

from students.models import Student, Attendance


def usage():
    print('Usage: python scripts/import_aggregated_attendance.py path/to/aggregated.csv')
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
    notfound = 0
    errors = []

    # fixed seed for reproducible distribution
    random.seed(12345)

    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=1):
            enr = (row.get('enrollment_no') or row.get('enrol') or row.get('Enrollment_No') or '').strip()
            if not enr:
                print(f'Row {i}: missing enrollment_no, skipping')
                skipped += 1
                continue
            try:
                total_s = int((row.get('Total_Sessions') or row.get('total_sessions') or row.get('total') or '').strip())
            except Exception:
                print(f'Row {i} ({enr}): invalid or missing Total_Sessions, skipping')
                skipped += 1
                continue

            # parse late/absent
            def to_int_field(names):
                for n in names:
                    v = row.get(n)
                    if v is None:
                        continue
                    v = v.strip()
                    if v == '':
                        continue
                    try:
                        return int(v)
                    except Exception:
                        # sometimes percentages or strings; ignore
                        try:
                            return int(float(v))
                        except Exception:
                            continue
                return 0

            late_count = to_int_field(['Late', 'late'])
            absent_count = to_int_field(['Absent', 'absent'])

            # if Present_Count provided directly
            present_count = None
            for key in ('Present_Count', 'Present', 'present_count'):
                if key in row and row[key] is not None and row[key].strip() != '':
                    try:
                        present_count = int(row[key].strip())
                        break
                    except Exception:
                        # maybe a percent string in Present_Rate; handle later
                        present_count = None
            if present_count is None:
                # try Present_Rate like '89%'
                pr = (row.get('Present_Rate') or row.get('present_rate') or '').strip()
                if pr.endswith('%'):
                    try:
                        pct = float(pr[:-1]) / 100.0
                        present_count = int(round(pct * total_s))
                    except Exception:
                        present_count = None

            if present_count is None:
                # fallback: compute from totals
                present_count = total_s - late_count - absent_count

            # sanity clamp
            if present_count < 0:
                present_count = 0
            if late_count < 0:
                late_count = 0
            if absent_count < 0:
                absent_count = 0

            # adjust if sums mismatch
            sum_counts = present_count + late_count + absent_count
            if sum_counts != total_s:
                # adjust present_count to fit total
                present_count = max(0, total_s - late_count - absent_count)

            notes = row.get('notes') or row.get('Notes') or ''

            # find student
            try:
                student = Student.objects.get(enrollment_no=enr)
            except Student.DoesNotExist:
                print(f'Row {i}: student {enr} not found in DB; skipping')
                notfound += 1
                continue

            # build status list
            statuses = ['present'] * present_count + ['late'] * late_count + ['absent'] * absent_count
            if len(statuses) == 0:
                print(f'Row {i}: no statuses for {enr}, skipping')
                skipped += 1
                continue

            # generate dates: last total_s days ending today
            today = datetime.utcnow().date()
            start_date = today - timedelta(days=total_s - 1)
            dates = [start_date + timedelta(days=d) for d in range(total_s)]

            # shuffle distribution reproducibly
            random.shuffle(statuses)

            # create / update attendance rows
            for date, status in zip(dates, statuses):
                try:
                    obj, created_flag = Attendance.objects.update_or_create(
                        student=student, date=date,
                        defaults={'status': status, 'notes': notes}
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f'Row {i} date {date}: {e}')

    print(f'Done. created={created}, updated={updated}, skipped={skipped}, notfound={notfound}')
    if errors:
        print('Some errors:')
        for e in errors[:10]:
            print('  ', e)
