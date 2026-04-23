from django.db.models import Count, Case, When, F, Value, FloatField, Q
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import Student, Attendance

def attendance_trend_data(request):
    # Get the last 30 days of attendance data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    attendance_by_date = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).values('date').annotate(
        total=Count('id'),
        present_count=Count(Case(When(status='present', then=1))),
        late_count=Count(Case(When(status='late', then=1)))
    ).annotate(
        present_rate=F('present_count') * 100.0 / F('total'),
        late_rate=F('late_count') * 100.0 / F('total')
    ).order_by('date')

    return JsonResponse({
        'dates': [x['date'].strftime('%Y-%m-%d') for x in attendance_by_date],
        'present_rates': [round(x['present_rate'], 1) for x in attendance_by_date],
        'late_rates': [round(x['late_rate'], 1) for x in attendance_by_date]
    })

def course_attendance_data(request):
    course_stats = Student.objects.values('course').annotate(
        total_attendance=Count('attendances'),
        present_count=Count(Case(
            When(attendances__status='present', then=1)
        ))
    ).annotate(
        present_rate=Case(
            When(total_attendance=0, then=Value(0.0)),
            default=F('present_count') * 100.0 / F('total_attendance'),
            output_field=FloatField(),
        )
    ).order_by('-present_rate')

    return JsonResponse({
        'courses': [x['course'] for x in course_stats],
        'rates': [round(x['present_rate'], 1) for x in course_stats]
    })

def attendance_hours_data(request):
    # Analyze attendance patterns by hour slots using ExtractHour
    attendance_by_hour = Attendance.objects.annotate(
        hour=ExtractHour('date')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Group into time slots
    slots = {
        'Morning (8-10)': 0,
        'Mid-day (10-12)': 0,
        'Afternoon (12-2)': 0,
        'Evening (2-4)': 0
    }
    
    for entry in attendance_by_hour:
        hour = entry['hour']
        count = entry['count']
        
        if 8 <= hour <= 10:
            slots['Morning (8-10)'] += count
        elif 10 < hour <= 12:
            slots['Mid-day (10-12)'] += count
        elif 12 < hour <= 14:
            slots['Afternoon (12-2)'] += count
        elif 14 < hour <= 16:
            slots['Evening (2-4)'] += count
    
    return JsonResponse({
        'labels': list(slots.keys()),
        'values': list(slots.values())
    })