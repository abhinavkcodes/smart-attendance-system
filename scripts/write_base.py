from pathlib import Path
p = Path(r"C:/Users/imabh/OneDrive/Desktop/FDS4/students/templates/students/base.html")
content = '''{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Student Tracker{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <!-- Local analytics/import styles -->
    <link rel="stylesheet" href="{% static 'students/css/analytics.css' %}">
    {% block head_extra %}{% endblock %}
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <!-- Logo and Primary Nav -->
                <div class="flex">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="{% url 'students:list' %}" class="flex items-center">
                            <i class="fas fa-graduation-cap text-blue-600 text-2xl mr-2"></i>
                            <span class="text-xl font-bold text-gray-800">StudentTracker</span>
                        </a>
                    </div>

                    <!-- Primary Navigation -->
                    <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                        <a href="{% url 'students:list' %}"
                           class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                           {% if request.resolver_match.url_name == 'list' %}
                               border-blue-500 text-gray-900
                           {% else %}
                               border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700
                           {% endif %}">
                            <i class="fas fa-users mr-2"></i>
                            All Students
                        </a>
                        <a href="{% url 'students:attendance_analytics' %}"
                           class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                           {% if request.resolver_match.url_name == 'attendance_analytics' %}
                               border-blue-500 text-gray-900
                           {% else %}
                               border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700
                           {% endif %}">
                            <i class="fas fa-chart-bar mr-2"></i>
                            Attendance Analytics
                        </a>
                    </div>
                </div>

                <!-- Secondary Navigation -->
                <div class="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-3">
                    <a href="{% url 'students:add' %}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <i class="fas fa-user-plus mr-2"></i>Add Student
                    </a>
                    <a href="{% url 'students:import_csv' %}" class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <i class="fas fa-file-import mr-2"></i>Import
                    </a>
                    <a href="{% url 'students:export_csv' %}" class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <i class="fas fa-file-export mr-2"></i>Export
                    </a>
                    <a href="/admin/" class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <i class="fas fa-cog mr-2"></i>Admin
                    </a>
                </div>

                <!-- Mobile menu button -->
                <div class="-mr-2 flex items-center sm:hidden">
                    <button type="button" class="mobile-menu-button inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500">
                        <i class="fas fa-bars"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Mobile menu -->
        <div class="sm:hidden mobile-menu hidden">
            <div class="pt-2 pb-3 space-y-1">
                <a href="{% url 'students:list' %}" 
                   class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium {% if request.resolver_match.url_name == 'list' %}border-blue-500 text-blue-700 bg-blue-50{% else %}border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800{% endif %}">
                    <i class="fas fa-users mr-2"></i>All Students
                </a>
                <a href="{% url 'students:add' %}" class="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:bg-gray-50 hover;border-gray-300 hover;text-gray-800">
                    <i class="fas fa-user-plus mr-2"></i>Add Student
                </a>
                <a href="{% url 'students:import_csv' %}" class="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:bg-gray-50 hover;border-gray-300 hover;text-gray-800">
                    <i class="fas fa-file-import mr-2"></i>Import CSV
                </a>
                <a href="{% url 'students:export_csv' %}" class="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:bg-gray-50 hover;border-gray-300 hover;text-gray-800">
                    <i class="fas fa-file-export mr-2"></i>Export CSV
                </a>
                <a href="/admin/" class="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:bg-gray-50 hover;border-gray-300 hover;text-gray-800">
                    <i class="fas fa-cog mr-2"></i>Admin
                </a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="py-6">
        {% if messages %}
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
            {% for message in messages %}
            <div class="rounded-lg p-4 {% if message.tags == 'success' %}bg-green-100 text-green-700
                         {% elif message.tags == 'error' %}bg-red-100 text-red-700
                         {% else %}bg-blue-100 text-blue-700{% endif %}">
                {{ message }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <script>
        // Mobile menu toggle
        document.addEventListener('DOMContentLoaded', function() {
            const button = document.querySelector('.mobile-menu-button');
            const menu = document.querySelector('.mobile-menu');
            if (button && menu) {
                button.addEventListener('click', () => {
                    menu.classList.toggle('hidden');
                });
            }
        });
    </script>

    <!-- Local analytics/import scripts -->
    <script src="{% static 'students/js/analytics.js' %}"></script>
</body>
</html>
'''
p.write_text(content, encoding='utf-8')
print('wrote', p)
