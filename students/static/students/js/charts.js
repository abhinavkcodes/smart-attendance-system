// Chart theme configuration
const chartTheme = {
    light: {
        backgroundColor: '#ffffff',
        borderColor: '#e5e7eb',
        textColor: '#1f2937',
        gridColor: '#f3f4f6'
    },
    dark: {
        backgroundColor: '#071020',
        borderColor: 'rgba(255,255,255,0.1)',
        textColor: '#e6eef8',
        gridColor: 'rgba(255,255,255,0.05)'
    }
};

// Apply theme to chart
function applyChartTheme(chart, isDark) {
    const theme = isDark ? chartTheme.dark : chartTheme.light;
    
    chart.options.plugins.legend.labels.color = theme.textColor;
    chart.options.scales.x.grid.color = theme.gridColor;
    chart.options.scales.x.ticks.color = theme.textColor;
    chart.options.scales.y.grid.color = theme.gridColor;
    chart.options.scales.y.ticks.color = theme.textColor;
    
    chart.update();
}

// Initialize trend chart
async function initTrendChart() {
    const response = await fetch('/students/api/charts/attendance/trend/');
    const data = await response.json();
    
    const ctx = document.getElementById('trendChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Present %',
                data: data.present_rates,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Late %',
                data: data.late_rates,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Percentage'
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });

    // Initialize with correct theme
    applyChartTheme(chart, document.documentElement.classList.contains('dark'));
    
    // Listen for theme changes
    document.documentElement.addEventListener('themeChanged', (e) => {
        applyChartTheme(chart, e.detail.isDark);
    });
}

// Initialize course attendance chart
async function initCourseChart() {
    const response = await fetch('/students/api/charts/attendance/course/');
    const data = await response.json();
    
    const ctx = document.getElementById('courseChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.courses,
            datasets: [{
                label: 'Present Rate %',
                data: data.rates,
                backgroundColor: '#3b82f6',
                borderColor: '#2563eb',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Course'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Present Rate %'
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });

    applyChartTheme(chart, document.documentElement.classList.contains('dark'));
    document.documentElement.addEventListener('themeChanged', (e) => {
        applyChartTheme(chart, e.detail.isDark);
    });
}

// Initialize hours distribution chart
async function initHoursChart() {
    const response = await fetch('/students/api/charts/attendance/hours/');
    const data = await response.json();
    
    const ctx = document.getElementById('hoursChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#3b82f6', // blue
                    '#10b981', // green
                    '#f59e0b', // yellow
                    '#ef4444', // red
                ],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
            }
        }
    });

    applyChartTheme(chart, document.documentElement.classList.contains('dark'));
    document.documentElement.addEventListener('themeChanged', (e) => {
        applyChartTheme(chart, e.detail.isDark);
    });
}

// Initialize all charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initTrendChart();
    initCourseChart();
    initHoursChart();
});