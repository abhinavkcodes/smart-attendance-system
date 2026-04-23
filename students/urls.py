from django.urls import path
from . import views
from .chart_views import attendance_trend_data, course_attendance_data, attendance_hours_data

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('add/', views.StudentCreateView.as_view(), name='add'),
    path('import/', views.import_students, name='import_csv'),
    path('export/', views.export_students, name='export_csv'),
    path('analytics/', views.analytics_page, name='analytics'),
    # Attendance management (site-facing)
    path('attendance/', views.attendance_page, name='attendance'),
    path('attendance/debug/', views.attendance_debug, name='attendance_debug'),
    path('attendance/export/', views.attendance_export, name='attendance_export'),
    path('attendance/analytics/', views.attendance_analytics_page, name='attendance_analytics'),
    path('attendance/low/', views.attendance_low_list, name='attendance_low_list'),
    path('charts/attendance/course.png', views.course_attendance_chart, name='course_attendance_chart'),
    path('charts/attendance/hours.png', views.attendance_hours_chart, name='attendance_hours_chart'),
    path('charts/attendance/trend.png', views.attendance_trend_chart, name='attendance_trend_chart'),
    # JSON API endpoints for Chart.js
    path('api/charts/attendance/trend/', attendance_trend_data, name='attendance_trend_data'),
    path('api/charts/attendance/course/', course_attendance_data, name='course_attendance_data'),
    path('api/charts/attendance/hours/', attendance_hours_data, name='attendance_hours_data'),
    path('charts/gpa.png', views.gpa_histogram, name='gpa_hist'),
    path('charts/enrollment.png', views.enrollment_trend, name='enrollment_trend'),
    path('charts/cgpa_analyzer.png', views.cgpa_analyzer, name='cgpa_analyzer'),
    path('charts/dept_heatmap.png', views.dept_cgpa_heatmap, name='dept_cgpa_heatmap'),
    path('charts/attendance/student/<int:pk>.png', views.attendance_student_chart, name='attendance_student_chart'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/attendance/', views.attendance_student_analytics, name='attendance_student_analytics'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
]