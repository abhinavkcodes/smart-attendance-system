# AI Agent Instructions for Student Management System

## Project Overview
This is a Django-based Student Management System with advanced data visualization capabilities. The system manages student records with features for CRUD operations, data import, and analytics.

## Key Components

### Data Model (`students/models.py`)
- Central `Student` model with comprehensive fields for academic and personal information
- Uses choices for constrained fields (Year: 1-5, Gender: M/F/O, Status: active/inactive/graduated)
- Implements soft timestamps (created_at/updated_at) for audit trails
- Photo uploads handled via ImageField to 'students/photos/'

### Views Architecture (`students/views.py`)
- Class-based views for CRUD operations (List/Detail/Create/Update/Delete)
- Advanced search implemented in `StudentListView` using Q objects
- Data visualization using matplotlib/seaborn for analytics
- Cached views for performance optimization

### URL Structure (`students/urls.py`)
- RESTful URL patterns under 'students/' namespace
- Analytics endpoints for different chart types (GPA, enrollment trends, etc.)

## Development Workflows

### Local Development
1. Ensure Django development server is running: `python manage.py runserver`
2. Media files for student photos are served from `/media/students/photos/`
3. Static files including CSS/JS are collected to `/static/`

### Data Management
- Bulk student import available via CSV upload at `/students/import/`
- Student photos are automatically resized and optimized on upload
- Search functionality supports partial matches across multiple fields

### Key Templates
- Base template: `students/templates/students/base.html`
- List view includes pagination (24 items per page)
- Form templates use custom widgets for date inputs and textareas

## Project Conventions

### Form Handling
- All forms extend `StudentForm` in `forms.py`
- Custom widgets used for:
  - Date fields: HTML5 date input
  - Phone numbers: Pattern-validated tel input
  - Text areas: Customized row counts

### Data Visualization
- All charts are server-side rendered using matplotlib
- Seaborn used for statistical visualizations
- Charts are cached for performance
- PNG format used for all chart exports

### URL Naming
- All URLs use the 'students' namespace
- View names follow pattern: list/detail/add/edit/delete
- Analytics URLs descriptively named (e.g., 'gpa_hist', 'enrollment_trend')

## Integration Points
- Media handling through Django's media files system
- Static file management via Django's staticfiles
- Database: SQLite for development (configured in settings.py)
- External libraries: matplotlib, seaborn for analytics

## Common Development Tasks
- Adding new student fields: Update Student model, forms.py, and relevant templates
- Adding new analytics: Create view function, add URL pattern, update analytics template
- Modifying search: Update get_queryset() in StudentListView