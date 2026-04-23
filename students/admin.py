from django.contrib import admin
from django.shortcuts import render
from django.utils.html import format_html
from django.db.models import Avg, Count
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('enrollment_no', 'first_name', 'last_name', 'email', 'course', 'year', 'status', 'created_at')
    list_filter = (
        'status',
        'course',
        'year',
        'gender',
        'admission_date',
    )
    search_fields = ('enrollment_no', 'first_name', 'last_name', 'email', 'course', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'gpa_comparison')
    date_hierarchy = 'admission_date'
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'enrollment_no', 'status',
                'first_name', 'last_name',
                'email', 'phone',
                'dob', 'gender'
            )
        }),
        ('Academic Information', {
            'fields': (
                'course', 'year',
                'gpa', 'admission_date'
            )
        }),
        ('Additional Details', {
            'fields': ('address', 'photo', 'notes')
        })
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        my_urls = [
            path('analytics/', self.admin_site.admin_view(self.analytics_view), name='analytics'),
        ]
        return my_urls + urls

    def analytics_view(self, request):
        # Set up the matplotlib figure
        plt.figure(figsize=(12, 5))
        
        # Create two subplots
        plt.subplot(1, 2, 1)
        
        # GPA Distribution
        gpas = list(Student.objects.filter(gpa__isnull=False).values_list('gpa', flat=True))
        if gpas:
            plt.hist(gpas, bins=20, color='skyblue', edgecolor='black')
            plt.title('GPA Distribution')
            plt.xlabel('GPA')
            plt.ylabel('Number of Students')
            plt.grid(True, alpha=0.3)
        
        # Course Distribution
        plt.subplot(1, 2, 2)
        course_data = Student.objects.values('course').annotate(count=Count('id'))
        courses = [item['course'] for item in course_data]
        counts = [item['count'] for item in course_data]
        if courses:
            plt.pie(counts, labels=courses, autopct='%1.1f%%')
            plt.title('Course Distribution')
        
        # Save the plot to a buffer
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        
        # Encode the image
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png).decode('utf-8')
        
        # Render the template
        context = {
            'title': 'Student Analytics',
            'graphic': graphic,
            'opts': self.model._meta,
        }
        return render(request, 'admin/students/analytics.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_analytics_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def student_info(self, obj):
        return format_html(
            '<div style="min-width:200px">'
            '<strong>{} {}</strong><br>'
            '<span style="color: #666;">{}</span>'
            '</div>',
            obj.first_name,
            obj.last_name,
            obj.email
        )
    student_info.short_description = 'Student'
    
    def course_info(self, obj):
        year_labels = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th'}
        return format_html(
            '<div style="min-width:150px">'
            '<strong>{}</strong><br>'
            '<span style="color: #666;">{} Year</span>'
            '</div>',
            obj.course,
            year_labels.get(obj.year, f'{obj.year}th')
        )
    course_info.short_description = 'Course & Year'
    
    def academic_status(self, obj):
        status_colors = {
            'active': 'green',
            'inactive': 'red',
            'graduated': 'blue'
        }
        gpa_color = 'green' if obj.gpa and obj.gpa >= 3.0 else 'orange'
        gpa_value = obj.gpa if obj.gpa is not None else 0
        return format_html(
            '<div style="min-width:120px">'
            '<span style="color: {};">{}</span><br>'
            '<strong style="color: {};">GPA: {:.2f}</strong>'
            '</div>',
            status_colors.get(obj.status, 'gray'),
            obj.get_status_display(),
            gpa_color,
            gpa_value
        )
    academic_status.short_description = 'Status & GPA'
    
    def contact_details(self, obj):
        return format_html(
            '<div style="min-width:150px">'
            '{}<br>'
            '<span style="color: #666;">{}</span>'
            '</div>',
            obj.phone or 'No phone',
            obj.address[:30] + '...' if obj.address and len(obj.address) > 30 else obj.address or 'No address'
        )
    contact_details.short_description = 'Contact'
    
    def gpa_comparison(self, obj):
        if obj.gpa is None:
            return "GPA not set"
        avg_gpa = Student.objects.filter(course=obj.course).aggregate(Avg('gpa'))['gpa__avg']
        if avg_gpa is None:
            return "No course average available"
        
        diff = obj.gpa - avg_gpa
        if diff > 0:
            color = 'green'
            symbol = '↑'
        elif diff < 0:
            color = 'red'
            symbol = '↓'
        else:
            color = 'gray'
            symbol = '−'
            
        return format_html(
            '<div style="color: {};">'
            'Course Avg: {:.2f}<br>'
            '{} {:.2f} points {}'
            '</div>',
            color,
            avg_gpa,
            symbol,
            abs(diff),
            'above average' if diff > 0 else 'below average' if diff < 0 else 'at average'
        )
    gpa_comparison.short_description = 'GPA Comparison'
    
    # Legacy performance_charts URL removed. Use the analytics view (registered earlier)
    
    def analytics_view(self, request):
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: GPA Distribution
        gpas = list(Student.objects.filter(gpa__isnull=False).values_list('gpa', flat=True))
        if gpas:
            sns.histplot(data=gpas, bins=20, ax=ax1, color='skyblue')
            ax1.set_title('GPA Distribution')
            ax1.set_xlabel('GPA')
            ax1.set_ylabel('Number of Students')
            ax1.grid(True, alpha=0.3)
        
        # Plot 2: Course Distribution
        course_data = Student.objects.values('course').annotate(count=Count('id'))
        courses = [item['course'] for item in course_data]
        counts = [item['count'] for item in course_data]
        if courses and counts:
            ax2.pie(counts, labels=courses, autopct='%1.1f%%')
            ax2.set_title('Course Distribution')
        
        # Save plots to buffer
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        
        # Encode the image
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png).decode('utf-8')
        
        context = {
            'title': 'Student Analytics',
            'graphic': graphic,
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/students/analytics.html', context)

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }