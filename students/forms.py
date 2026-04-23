from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'enrollment_no', 'first_name', 'last_name', 'email',
            'dob', 'course', 'year', 'status', 'gpa',
            'gender', 'phone', 'address', 'admission_date',
            'photo', 'notes'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'pattern': '[0-9+\- ]*'}),
        }
