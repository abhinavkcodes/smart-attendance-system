from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q, Count, Avg, Case, When, F, FloatField, Value
from .chart_views import attendance_trend_data, course_attendance_data, attendance_hours_data
from django.db.models.functions import ExtractYear
from django.views.decorators.cache import cache_page

import csv
import io
import datetime
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from .models import Student
from .models import Attendance
from .forms import StudentForm

from django.shortcuts import render, redirect

class StudentListView(ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 24

    def get_queryset(self):
        qs = Student.objects.all().order_by('-id')
        # allow filtering by free-text search (search or q) and by status
        q = self.request.GET.get('search') or self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(enrollment_no__icontains=q) |
                Q(email__icontains=q) |
                Q(course__icontains=q) |
                Q(status__icontains=q)
            )
        if status:
            qs = qs.filter(status__iexact=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Use the full (un-sliced) queryset for aggregate counts so pagination
        # slicing doesn't prevent further filtering (sliced QuerySets raise
        # "Cannot filter a query once a slice has been taken").
        full_qs = self.get_queryset()

        # filtered counts
        total_students = full_qs.count()
        active_students = full_qs.filter(status__iexact='active').count()
        graduated_students = full_qs.filter(status__iexact='graduated').count()
        inactive_students = full_qs.filter(status__iexact='inactive').count()

        # overall counts (unfiltered)
        total_all_students = Student.objects.count()
        total_all_active = Student.objects.filter(status__iexact='active').count()
        total_all_graduated = Student.objects.filter(status__iexact='graduated').count()
        total_all_inactive = Student.objects.filter(status__iexact='inactive').count()

        ctx.update({
            'total_students': total_students,
            'active_students': active_students,
            'graduated_students': graduated_students,
            'inactive_students': inactive_students,
            'total_all_students': total_all_students,
            'total_all_active': total_all_active,
            'total_all_graduated': total_all_graduated,
            'total_all_inactive': total_all_inactive,
            'debug_info': {
                'search_term': self.request.GET.get('search') or self.request.GET.get('q') or '',
                'total_count': total_students,
                'status_counts': {
                    'active': active_students,
                    'graduated': graduated_students,
                    'inactive': inactive_students,
                }
            }
            , 'current_status': self.request.GET.get('status') or ''
        })
        return ctx

class StudentDetailView(DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add attendance stats if any exist
        attendance = self.object.attendances.all()
        total = attendance.count()
        present = attendance.filter(status='present').count()
        late = attendance.filter(status='late').count()
        absent = attendance.filter(status='absent').count()
        context.update({
            'attendance_stats': {
                'total': total,
                'present': present,
                'late': late,
                'absent': absent,
                'present_pct': round((present / total * 100) if total else 0, 1)
            }
        })
        return context

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:list')

def import_students(request):
    """
    CSV importer. Accepted headers (flexible):
    first_name,last_name,enrollment_no,email,gpa,course,year,status,phone,address,dob,admission_date,gender
    """
    if request.method == 'POST':
        # accept either 'file' or 'csv_file' from templates (backwards compatible)
        uploaded = request.FILES.get('file') or request.FILES.get('csv_file')
        if not uploaded:
            messages.error(request, "No file uploaded.")
            return redirect('students:list')
        try:
            raw = uploaded.read().decode('utf-8')
        except Exception:
            messages.error(request, "Unable to read file. Make sure it's UTF-8 encoded.")
            return redirect('students:list')

        reader = csv.DictReader(io.StringIO(raw))
        created = 0
        errors = []
        with transaction.atomic():
            for i, row in enumerate(reader, start=1):
                try:
                    def get(*names):
                        for n in names:
                            v = row.get(n)
                            if v not in (None, ''):
                                return v.strip()
                        return None

                    fn = get('first_name', 'firstname', 'first') or ''
                    ln = get('last_name', 'lastname', 'last') or ''
                    enr = get('enrollment_no', 'enrollment', 'reg_no', 'registration_no') or ''
                    email = get('email') or ''
                    gpa = get('gpa', 'cgpa')
                    course = get('course', 'major') or ''
                    year = get('year', 'class')
                    status = (get('status') or 'active').lower()
                    phone = get('phone', 'contact') or ''
                    address = get('address') or ''
                    dob_s = get('dob', 'date_of_birth')
                    admission_s = get('admission_date', 'admitted')
                    gender = get('gender') or ''

                    gpa_val = float(gpa) if gpa else None
                    year_val = int(year) if year else None

                    def parse_date(s):
                        if not s:
                            return None
                        s = s.strip()
                        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y'):
                            try:
                                return datetime.datetime.strptime(s, fmt).date()
                            except Exception:
                                continue
                        return None

                    dob_val = parse_date(dob_s)
                    admission_val = parse_date(admission_s)

                    Student.objects.create(
                        first_name=fn,
                        last_name=ln,
                        enrollment_no=enr,
                        email=email,
                        gpa=gpa_val,
                        course=course,
                        year=year_val,
                        status=status,
                        phone=phone,
                        address=address,
                        dob=dob_val,
                        admission_date=admission_val,
                        gender=gender
                    )
                    created += 1
                except Exception as e:
                    errors.append(f'Row {i}: {str(e)}')

        if created:
            messages.success(request, f'Imported {created} students.')
        if errors:
            messages.error(request, 'Some rows failed: ' + '; '.join(errors[:5]))
        return redirect('students:list')

    # render the CSV import template
    return render(request, 'students/import_csv.html')


def export_students(request):
    """Export all students as CSV. Used by the UI link named 'export_csv'."""
    # support optional filtering via query params (status, search/q)
    qs = Student.objects.all().order_by('id')
    status = request.GET.get('status')
    q = request.GET.get('search') or request.GET.get('q')
    if status:
        qs = qs.filter(status__iexact=status)
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(enrollment_no__icontains=q) |
            Q(email__icontains=q) |
            Q(course__icontains=q) |
            Q(status__icontains=q)
        )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['id', 'enrollment_no', 'first_name', 'last_name', 'email', 'course', 'year', 'status', 'gpa'])
    for s in qs:
        writer.writerow([s.id, s.enrollment_no, s.first_name, s.last_name, s.email, s.course, s.year, s.status, s.gpa])
    resp = HttpResponse(buf.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="students_export.csv"'
    return resp

# Charts (return PNG images)
@cache_page(60 * 60)
def gpa_histogram(request):
    gpas = list(Student.objects.filter(gpa__isnull=False).values_list('gpa', flat=True))
    if not gpas:
        return HttpResponse(status=204)
    plt.figure(figsize=(6,4))
    sns.set_style("whitegrid")
    sns.histplot(gpas, bins=10, kde=True, color='#3b82f6')
    plt.title('GPA Distribution')
    plt.xlabel('GPA')
    plt.ylabel('Count')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

@cache_page(60 * 60)
def enrollment_trend(request):
    qs = Student.objects.filter(admission_date__isnull=False).annotate(year=ExtractYear('admission_date')) \
           .values('year').annotate(count=Count('id')).order_by('year')
    years = [row['year'] for row in qs]
    counts = [row['count'] for row in qs]
    if not years:
        return HttpResponse(status=204)
    plt.figure(figsize=(7,4))
    sns.lineplot(x=years, y=counts, marker='o', color='#10b981')
    plt.title('Enrollment Trend by Year')
    plt.xlabel('Year')
    plt.ylabel('Students Enrolled')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

@cache_page(60 * 60)
def cgpa_analyzer(request):
    qs = Student.objects.filter(gpa__isnull=False)
    if not qs.exists():
        return HttpResponse(status=204)
    years = [s.year if s.year else 0 for s in qs]
    gpas = [s.gpa for s in qs]
    depts = [s.course or 'Unknown' for s in qs]
    plt.figure(figsize=(10,5))
    sns.set_style("whitegrid")
    unique_depts = list(dict.fromkeys(depts))
    palette = sns.color_palette("tab10", n_colors=max(3, len(unique_depts)))
    sns.scatterplot(x=years, y=gpas, hue=depts, palette=palette, alpha=0.8, s=60, edgecolor='w')
    plt.xlabel("Year")
    plt.ylabel("CGPA")
    plt.ylim(0, 4.5)
    plt.title("Smart CGPA Analyzer — CGPA by Year and Department")
    plt.legend(title="Department", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")

@cache_page(60 * 60)
def dept_cgpa_heatmap(request):
    qs = Student.objects.filter(gpa__isnull=False)
    if not qs.exists():
        return HttpResponse(status=204)
    courses = list(qs.values_list('course', flat=True).distinct())
    years = sorted(set([s.year if s.year else 0 for s in qs]))
    courses_sorted = sorted([c if c else 'Unknown' for c in courses])
    matrix = []
    for course in courses_sorted:
        row = []
        for y in years:
            avg = qs.filter(course=course, year=y).aggregate(avg_gpa=Avg('gpa'))['avg_gpa']
            row.append(avg if avg is not None else np.nan)
        matrix.append(row)
    data = np.array(matrix, dtype=float)
    if data.size == 0 or np.all(np.isnan(data)):
        return HttpResponse(status=204)
    plt.figure(figsize=(max(6, len(years)*1.2), max(4, len(courses_sorted)*0.35) + 2))
    sns.set(font_scale=0.9)
    ax = sns.heatmap(data, annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Avg CGPA'},
                     linewidths=0.5, linecolor='white', vmin=0, vmax=4.5,
                     xticklabels=years, yticklabels=courses_sorted)
    ax.set_xlabel("Year")
    ax.set_ylabel("Department / Course")
    plt.title("Department-wise Average CGPA Heatmap")
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")

def analytics_page(request):
    return render(request, 'students/analytics.html')


def attendance_page(request):
    """Site-facing attendance management page. Not part of admin.
    GET: show list of students and attendance for selected date (default today)
    POST: accept attendance submissions as POST data: status_<student_id>=present|absent|late
    """
    date_str = request.GET.get('date')
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            date = datetime.date.today()
    else:
        date = datetime.date.today()

    students = Student.objects.filter(status='active').order_by('enrollment_no')

    if request.method == 'POST':
        # process attendance
        submitted = 0
        for student in students:
            key = f'status_{student.id}'
            status = request.POST.get(key)
            if status not in ('present', 'absent', 'late'):
                continue
            obj, created = Attendance.objects.update_or_create(
                student=student, date=date,
                defaults={'status': status, 'notes': request.POST.get(f'notes_{student.id}', '')}
            )
            submitted += 1
        messages.success(request, f'Attendance recorded for {submitted} students for {date}.')
        return redirect('students:attendance')

    # prepare existing attendance dict and rows for template
    existing = Attendance.objects.filter(date=date).select_related('student')
    attendance_map = {a.student_id: a for a in existing}
    rows = []
    for student in students:
        rows.append((student, attendance_map.get(student.id)))

    context = {
        'students_rows': rows,
        'date': date,
    }
    return render(request, 'students/attendance.html', context)


def attendance_debug(request):
    """Debug endpoint: return a plain-text dump of students and existing attendance for the date.
    Use this to isolate whether the error is in view logic or template rendering.
    """
    date_str = request.GET.get('date')
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            date = datetime.date.today()
    else:
        date = datetime.date.today()

    students = Student.objects.filter(status='active').order_by('enrollment_no')
    existing = Attendance.objects.filter(date=date).select_related('student')
    attendance_map = {a.student_id: a for a in existing}

    lines = [f"Attendance debug for {date}:\n"]
    for student in students:
        a = attendance_map.get(student.id)
        status = a.status if a else 'N/A'
        notes = a.notes if a else ''
        lines.append(f"{student.enrollment_no}\t{student.first_name} {student.last_name}\t{status}\t{notes}")

    return HttpResponse('\n'.join(lines), content_type='text/plain')


def course_attendance_chart(request):
    """Return a bar chart showing attendance percentage by course."""
    from django.db.models import Count, Case, When, FloatField
    
    # Get course-wise attendance stats
    stats = Student.objects.values('course').annotate(
        total_attendance=Count('attendances'),
        present_count=Count(Case(
            When(attendances__status='present', then=1),
            output_field=FloatField(),
        )),
    ).filter(total_attendance__gt=0)  # only courses with attendance records
    
    if not stats:
        return HttpResponse(status=204)
        
    courses = [s['course'] or 'Unknown' for s in stats]
    percentages = [round((s['present_count'] / s['total_attendance'] * 100), 1) if s['total_attendance'] > 0 else 0 
                  for s in stats]
    
    plt.style.use('seaborn')
    plt.figure(figsize=(10, 5))
    
    # Create bar chart with gradient
    bars = plt.bar(courses, percentages)
    
    # Color bars based on percentage (red to green gradient)
    for bar, percentage in zip(bars, percentages):
        if percentage >= 75:
            bar.set_color('#48bb78')  # green
        elif percentage >= 60:
            bar.set_color('#4299e1')  # blue
        else:
            bar.set_color('#f56565')  # red
    
    plt.axhline(y=75, color='#48bb78', linestyle='--', alpha=0.5, label='Target (75%)')
    plt.grid(True, axis='y', alpha=0.3)
    
    plt.title('Course-wise Attendance Percentage', pad=20, fontsize=12, fontweight='bold')
    plt.xlabel('Course', labelpad=10)
    plt.ylabel('Attendance %', labelpad=10)
    
    # Rotate labels and adjust layout
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    
    # Add percentage labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

def attendance_hours_chart(request):
    """Return a pie chart showing present vs absent hours distribution."""
    from django.db.models import Count
    
    # Get overall attendance counts
    stats = Attendance.objects.aggregate(
        present=Count(Case(When(status='present', then=1))),
        absent=Count(Case(When(status='absent', then=1))),
        late=Count(Case(When(status='late', then=1)))
    )
    
    if not any(stats.values()):
        return HttpResponse(status=204)
    
    # Create pie chart with improved styling
    plt.style.use('seaborn')
    plt.figure(figsize=(8, 8), facecolor='white')
    
    labels = ['Present', 'Absent', 'Late']
    sizes = [stats['present'], stats['absent'], stats['late']]
    colors = ['#48bb78', '#f56565', '#ecc94b']
    explode = (0.02, 0.02, 0.02)  # slight separation between segments
    
    # Create donut chart with custom styling
    wedges, texts, autotexts = plt.pie(sizes, 
                                      explode=explode,
                                      labels=labels,
                                      colors=colors,
                                      autopct='%1.1f%%',
                                      startangle=90,
                                      wedgeprops={'width': 0.7, 'edgecolor': 'white', 'linewidth': 2},
                                      pctdistance=0.75,
                                      textprops={'fontsize': 12})
    
    # Style percentage labels
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.setp(texts, size=12)
    
    # Add total hours in center
    total_hours = sum(sizes)
    plt.text(0, 0, f'Total\n{total_hours}', 
            ha='center', va='center',
            fontsize=12, fontweight='bold')
    
    plt.title('Attendance Hours Distribution', pad=20, fontsize=14, fontweight='bold')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

def attendance_trend_chart(request):
    """Return a line chart showing attendance trend over time."""
    from django.db.models import Count, Case, When, F
    from django.db.models.functions import TruncDate
    
    # Get daily attendance stats for the last 30 days
    # The Attendance.date field is already a DateField, so we can group by it directly
    stats = Attendance.objects.values('date').annotate(
        total=Count('id'),
        present=Count(Case(When(status='present', then=1))),
        absent=Count(Case(When(status='absent', then=1))),
        late=Count(Case(When(status='late', then=1)))
    ).order_by('date')
    
    if not stats:
        return HttpResponse(status=204)
    
    # Prepare data
    dates = [s['date'] for s in stats]
    present_rates = [s['present'] / s['total'] * 100 for s in stats]
    late_rates = [s['late'] / s['total'] * 100 for s in stats]
    
    # Create trend chart
    # prefer seaborn styling when available via the sns wrapper; fallback to matplotlib defaults
    try:
        sns.set_style('whitegrid')
    except Exception:
        pass
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Plot lines with gradient fill
    ax.fill_between(dates, present_rates, alpha=0.2, color='#48bb78', label='Present %')
    ax.plot(dates, present_rates, color='#48bb78', linewidth=2, marker='o')
    
    ax.fill_between(dates, late_rates, alpha=0.2, color='#ecc94b', label='Late %')
    ax.plot(dates, late_rates, color='#ecc94b', linewidth=2, marker='o')
    
    # Styling
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    plt.title('Attendance Trend Over Time', pad=20, fontsize=14, fontweight='bold')
    plt.xlabel('Date', labelpad=10)
    plt.ylabel('Percentage', labelpad=10)
    
    # Rotate date labels
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')

def attendance_analytics_page(request):
    """Show analytics dashboard with attendance charts."""
    from django.db.models import Count, Case, When, Avg, F
    from django.db.models.functions import ExtractMonth, ExtractYear
    
    # Get summary stats
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    
    # Get recent attendance trend with more details
    recent_stats = Attendance.objects.values('date').annotate(
        total=Count('id'),
        present=Count(Case(When(status='present', then=1))),
        late=Count(Case(When(status='late', then=1))),
        absent=Count(Case(When(status='absent', then=1))),
    ).order_by('-date')[:7]
    
    # Get course-wise detailed stats
    course_stats = Student.objects.values('course').annotate(
        total_students=Count('id'),
        total_attendance=Count('attendances'),
        present_count=Count(Case(When(attendances__status='present', then=1))),
        late_count=Count(Case(When(attendances__status='late', then=1))),
        absent_count=Count(Case(When(attendances__status='absent', then=1))),
    ).filter(total_attendance__gt=0).order_by('-total_students')

    # Calculate monthly trends
    monthly_stats = Attendance.objects.annotate(
        month=ExtractMonth('date'),
        year=ExtractYear('date')
    ).values('month', 'year').annotate(
        total=Count('id'),
        present=Count(Case(When(status='present', then=1))),
    ).order_by('year', 'month')[:12]  # last 12 months
    
    # Add percentage calculations
    for stat in course_stats:
        if stat['total_attendance'] > 0:
            stat['present_rate'] = round((stat['present_count'] / stat['total_attendance']) * 100, 1)
            stat['late_rate'] = round((stat['late_count'] / stat['total_attendance']) * 100, 1)
            stat['absent_rate'] = round((stat['absent_count'] / stat['total_attendance']) * 100, 1)
        else:
            stat['present_rate'] = stat['late_rate'] = stat['absent_rate'] = 0

    context = {
        'total_students': total_students,
        'active_students': active_students,
        'recent_stats': recent_stats,
        'course_stats': course_stats,
        'monthly_stats': monthly_stats,
        # Add overall stats
        'overall_stats': {}
    }
    # compute overall aggregates safely
    from django.db.models import F, Value
    from django.db.models.functions import Coalesce

    agg = Attendance.objects.aggregate(
        total=Count('id'),
        present=Count(Case(When(status='present', then=1)))
    )
    total_sessions = agg.get('total') or 0
    present_count = agg.get('present') or 0
    present_rate = round((present_count * 100.0 / total_sessions), 1) if total_sessions > 0 else 0

    # compute low attendance students: annotate per-student present/total then filter
    students_with_rates = Student.objects.annotate(
        total_attendance=Count('attendances'),
        present_count=Count(Case(When(attendances__status='present', then=1)))
    ).filter(total_attendance__gt=0).annotate(
        attendance_rate=F('present_count') * Value(100.0) / F('total_attendance')
    )
    low_attendance_students = students_with_rates.filter(attendance_rate__lt=75).count()

    # finalize overall_stats
    context['overall_stats'] = {
        'total_sessions': total_sessions,
        'present_rate': present_rate,
        'courses_count': Student.objects.values('course').distinct().count(),
        'low_attendance_students': low_attendance_students,
    }

    return render(request, 'students/attendance_analytics.html', context)


def attendance_low_list(request):
    """Return JSON list of students with attendance rate below a threshold (default 75%)."""
    from django.db.models import Count, Case, When, F, Value
    threshold = int(request.GET.get('threshold', 75))

    students_with_rates = Student.objects.annotate(
        total_attendance=Count('attendances'),
        present_count=Count(Case(When(attendances__status='present', then=1)))
    ).filter(total_attendance__gt=0).annotate(
        attendance_rate=F('present_count') * Value(100.0) / F('total_attendance')
    ).filter(attendance_rate__lt=threshold).order_by('attendance_rate')

    data = []
    for s in students_with_rates:
        data.append({
            'id': s.id,
            'enrollment_no': s.enrollment_no,
            'first_name': s.first_name,
            'last_name': s.last_name,
            'course': s.course,
            'year': s.year,
            'total_attendance': s.total_attendance,
            'present_count': s.present_count,
            'attendance_rate': round(float(s.attendance_rate), 1)
        })

    return JsonResponse({'students': data})

def attendance_export(request):
    """Export attendance CSV for a given date (query param 'date' in YYYY-MM-DD)."""
    date_str = request.GET.get('date')
    if not date_str:
        return HttpResponse('Provide ?date=YYYY-MM-DD', status=400)
    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return HttpResponse('Invalid date format, use YYYY-MM-DD', status=400)

    qs = Attendance.objects.filter(date=date).select_related('student')
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['enrollment_no', 'first_name', 'last_name', 'email', 'course', 'year', 'status', 'notes'])
    for a in qs:
        s = a.student
        writer.writerow([s.enrollment_no, s.first_name, s.last_name, s.email, s.course, s.year, a.status, a.notes])
    resp = HttpResponse(buf.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="attendance_{date}.csv"'
    return resp


@cache_page(60 * 10)
def attendance_student_chart(request, pk):
    """Return a small PNG chart showing attendance history for a single student.
    Mapping: present=1, late=0.5, absent=0
    """
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return HttpResponse(status=404)

    qs = Attendance.objects.filter(student=student).order_by('date')
    if not qs.exists():
        return HttpResponse(status=204)

    dates = [a.date for a in qs]
    values = []
    for a in qs:
        if a.status == 'present':
            values.append(1.0)
        elif a.status == 'late':
            values.append(0.5)
        else:
            values.append(0.0)

    plt.figure(figsize=(8,3))
    sns.set_style('whitegrid')
    plt.plot(dates, values, marker='o', linestyle='-', color='#6366f1')
    plt.ylim(-0.1, 1.05)
    plt.yticks([0, 0.5, 1], ['Absent', 'Late', 'Present'])
    plt.title(f'Attendance — {student.first_name} {student.last_name}')
    plt.xlabel('Date')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def attendance_student_analytics(request, pk):
    """Render a simple analytics page for a single student that embeds the chart above
    and shows simple counts (present/absent/late).
    """
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('students:list')

    qs = Attendance.objects.filter(student=student)
    total = qs.count()
    present = qs.filter(status='present').count()
    absent = qs.filter(status='absent').count()
    late = qs.filter(status='late').count()

    pct = (present / total * 100) if total else 0

    context = {
        'student': student,
        'total_records': total,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'present_pct': round(pct, 1),
        # chart URL
        'chart_url': reverse_lazy('students:attendance_student_chart', args=[student.pk])
    }
    # include row listing for template
    context['attendance_rows'] = qs.order_by('-date')
    return render(request, 'students/attendance_student.html', context)