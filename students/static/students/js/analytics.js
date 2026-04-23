// JavaScript functions for attendance analytics interactivity

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Add tooltip functionality
    const tooltips = document.querySelectorAll('.has-tooltip');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
});

// Tooltip functions
function showTooltip(e) {
    const tooltip = e.currentTarget.querySelector('.tooltip');
    tooltip.style.opacity = '1';
    tooltip.style.visibility = 'visible';
}

function hideTooltip(e) {
    const tooltip = e.currentTarget.querySelector('.tooltip');
    tooltip.style.opacity = '0';
    tooltip.style.visibility = 'hidden';
}

// Detail view functions
function showStudentDetails() {
    // Implement modal or detail view for student distribution
    console.log('Showing student details');
    // TODO: Add AJAX call to fetch detailed student data
}

function showAttendanceDetails() {
    // Implement modal or detail view for attendance statistics
    console.log('Showing attendance details');
    // TODO: Add AJAX call to fetch detailed attendance data
}

function showTodayDetails() {
    // Implement modal or detail view for today's attendance
    console.log('Showing today\'s details');
    // TODO: Add AJAX call to fetch detailed today's data
}

function showAttentionDetails() {
    console.log('Showing attention required details');
    // Fetch students below threshold (default 75)
    fetch('/students/attendance/low/?threshold=75')
        .then(resp => {
            if (!resp.ok) throw new Error('Network response was not ok');
            return resp.json();
        })
        .then(data => {
            const tbody = document.querySelector('#attention-table tbody');
            tbody.innerHTML = '';
            if (!data.students || data.students.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td class="px-3 py-2" colspan="6">No students found below threshold.</td>';
                tbody.appendChild(tr);
            } else {
                data.students.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.className = 'border-b';
                    tr.innerHTML = `
                        <td class="px-3 py-2">${s.enrollment_no}</td>
                        <td class="px-3 py-2">${s.first_name} ${s.last_name}</td>
                        <td class="px-3 py-2">${s.course}</td>
                        <td class="px-3 py-2">${s.present_count}</td>
                        <td class="px-3 py-2">${s.total_attendance}</td>
                        <td class="px-3 py-2">${s.attendance_rate}%</td>
                    `;
                    // Clicking a row navigates to student detail
                    tr.style.cursor = 'pointer';
                    tr.addEventListener('click', () => {
                        window.location.href = `/students/${s.id}/attendance/`;
                    });
                    tbody.appendChild(tr);
                });
            }
            openAttentionModal();
        })
        .catch(err => {
            console.error('Failed to load attention data', err);
            alert('Failed to load student list. See console for details.');
        });
}

function openAttentionModal() {
    const modal = document.getElementById('attention-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeAttentionModal() {
    const modal = document.getElementById('attention-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Import form helpers
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('#import-file-input');
    const chooseBtn = document.querySelector('#choose-file-btn');
    const fileNameSpan = document.querySelector('#selected-file-name');
    const uploadBtn = document.querySelector('#upload-btn');
    const importForm = document.querySelector('#import-form');

    if (!fileInput) return; // nothing to do on pages without the import form

    // Click handler for custom choose button
    if (chooseBtn) {
        chooseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
        });
    }

    // Show selected file name and enable upload
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            fileNameSpan.textContent = file.name;
            uploadBtn.disabled = false;
            uploadBtn.setAttribute('aria-disabled', 'false');
        } else {
            fileNameSpan.textContent = 'No file chosen';
            uploadBtn.disabled = true;
            uploadBtn.setAttribute('aria-disabled', 'true');
        }
    });

    // On submit, show spinner and disable inputs (preserve accessible text)
    if (importForm) {
        importForm.addEventListener('submit', function() {
            uploadBtn.disabled = true;
            uploadBtn.setAttribute('aria-disabled', 'true');
            uploadBtn.setAttribute('aria-busy', 'true');
            const btnText = uploadBtn.querySelector('.btn-text');
            const spinner = uploadBtn.querySelector('.spinner');
            if (btnText) btnText.textContent = 'Uploading...';
            if (spinner) spinner.classList.remove('hidden');
            if (chooseBtn) chooseBtn.disabled = true;
        });
    }
});