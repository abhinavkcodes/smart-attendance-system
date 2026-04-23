# Smart Attendance & Analytics System

A Django-based web application for managing student attendance and visualizing data using server-rendered templates.

---

## Features
- Student attendance tracking
- Data visualization using charts (bar and pie)
- Attendance import via scripts
- Server-side rendered UI using Django templates

---

## Tech Stack
- Backend: Django (Python)
- Frontend: HTML, CSS, JavaScript (Django templates)
- Database: SQLite

---

## Project Structure


│── myproject/        # Django project configuration  
│── students/         # Core application  
│── scripts/          # Utility scripts  
│── manage.py  

---

## Setup Instructions

git clone https://github.com/abhinavkcodes/smart-attendance-system.git  
cd smart-attendance-system  

python -m venv venv  
venv\Scripts\activate  

pip install -r requirements.txt  

python manage.py migrate  
python manage.py runserver  

---

## Future Improvements
- Add authentication system (login/register)
- Build REST APIs using Django REST Framework
- Improve UI/UX
- Add predictive analytics for attendance trends

---

## Author
Abhinav Kumar
