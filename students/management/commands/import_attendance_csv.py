import csv
import os
import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from students.models import Student, Attendance


class Command(BaseCommand):
    help = 'Import attendance aggregates from a CSV and create per-day Attendance records (approximation)'

    def add_arguments(self, parser):
        parser.add_argument('--path', '-p', required=True, help='Path to the CSV file')
        parser.add_argument('--dry-run', action='store_true', help='Do not write to the database')

    def handle(self, *args, **options):
        path = options['path']
        dry = options['dry_run']

        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created = 0
        updated = 0
        skipped = 0
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader, start=1):
                enr = (row.get('enrollment_no') or '').strip()
                if not enr:
                    self.stderr.write(f'Row {i}: missing enrollment_no, skipping')
                    skipped += 1
                    continue

                try:
                    student = Student.objects.filter(enrollment_no__iexact=enr).first()
                    if not student:
                        # If student missing, create a minimal record using available fields
                        student = Student.objects.create(
                            enrollment_no=enr,
                            first_name=(row.get('first_name') or 'Unknown').strip(),
                            last_name=(row.get('last_name') or '').strip(),
                            email=(row.get('email') or f'{enr}@example.com').strip(),
                            course=(row.get('course') or 'Unknown').strip(),
                            status='active'
                        )

                    # Parse counts
                    total_s = row.get('Total_Sessions') or row.get('total_sessions') or ''
                    try:
                        total = int(float(total_s)) if total_s != '' else 0
                    except Exception:
                        total = 0

                    present_rate_s = row.get('Present_Rate') or row.get('present_rate') or ''
                    try:
                        present_rate = float(present_rate_s)
                    except Exception:
                        present_rate = None

                    late_s = row.get('Late') or row.get('late') or ''
                    absent_s = row.get('Absent') or row.get('absent') or ''
                    try:
                        late = int(float(late_s)) if late_s != '' else 0
                    except Exception:
                        late = 0
                    try:
                        absent = int(float(absent_s)) if absent_s != '' else 0
                    except Exception:
                        absent = 0

                    # Compute present count
                    if total > 0:
                        if late or absent:
                            present = max(0, total - late - absent)
                        elif present_rate is not None:
                            present = round(total * (present_rate / 100.0))
                        else:
                            present = total - late - absent
                    else:
                        present = 0

                    # Build status list and map onto last `total` days
                    statuses = []
                    statuses.extend(['present'] * present)
                    statuses.extend(['late'] * late)
                    statuses.extend(['absent'] * absent)

                    # If sizes mismatch, normalize
                    if total and len(statuses) != total:
                        # fill with 'present' to match total
                        while len(statuses) < total:
                            statuses.append('present')
                        if len(statuses) > total:
                            statuses = statuses[:total]

                    # Deterministic shuffle per student for distribution
                    seed = sum(ord(c) for c in enr)
                    rnd = random.Random(seed)
                    rnd.shuffle(statuses)

                    today = timezone.now().date()
                    dates = [today - timedelta(days=d) for d in range(total)]

                    # Create or update Attendance entries
                    for dt, status in zip(dates, statuses):
                        if dry:
                            continue
                        obj, created_flag = Attendance.objects.update_or_create(
                            student=student,
                            date=dt,
                            defaults={'status': status, 'notes': 'Imported from CSV'}
                        )
                        if created_flag:
                            created += 1
                        else:
                            updated += 1

                except Exception as e:
                    self.stderr.write(f'Row {i} error: {e}')
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Import complete. created={created} updated={updated} skipped={skipped}'))