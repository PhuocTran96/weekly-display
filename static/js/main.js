// Weekly Display Tracking Web Application JavaScript

// Global variables
let currentSessionId = null;
let currentJobId = null;
let statusCheckInterval = null;
let uploadedFiles = {
    raw: null,
    report: null
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing web application...');
    initializeEventListeners();
    initializeUIEnhancements();
});

function initializeEventListeners() {
    // File upload form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFileUpload);
    }

    // File input change listeners
    const rawDisplayFile = document.getElementById('rawDisplayFile');
    const reportWeekFile = document.getElementById('reportWeekFile');

    if (rawDisplayFile) {
        rawDisplayFile.addEventListener('change', function(e) {
            updateFileStatus('rawDisplayStatus', e.target.files[0]);
            uploadedFiles.raw = e.target.files[0];
            checkUploadReadiness();
        });
    }

    if (reportWeekFile) {
        reportWeekFile.addEventListener('change', function(e) {
            updateFileStatus('reportWeekStatus', e.target.files[0]);
            uploadedFiles.report = e.target.files[0];
            checkUploadReadiness();
        });
    }

    // Process button
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.addEventListener('click', startProcessing);
    }

    // Download links
    const exportAlertsBtn = document.getElementById('exportAlertsBtn');
    if (exportAlertsBtn) {
        exportAlertsBtn.addEventListener('click', exportAlerts);
    }

    // Alert filter and search
    const alertFilter = document.getElementById('alertFilter');
    const searchInput = document.getElementById('searchInput');

    if (alertFilter) {
        alertFilter.addEventListener('change', filterAlerts);
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterAlerts, 300));
    }
}

function initializeUIEnhancements() {
    // Add drag and drop functionality
    setupDragAndDrop();

    // Initialize progress bars
    resetProgressBar();

    // Check for existing session data
    checkExistingSession();
}

function setupDragAndDrop() {
    const uploadAreas = document.querySelectorAll('.upload-area');

    uploadAreas.forEach(area => {
        const fileInput = area.querySelector('.file-input');

        if (!fileInput) return;

        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('drag-over');
        });

        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('drag-over');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
                    fileInput.files = files;
                    fileInput.dispatchEvent(new Event('change'));
                } else {
                    showNotification('Please select a CSV file', 'error');
                }
            }
        });
    });
}

async function handleFileUpload(e) {
    e.preventDefault();

    const formData = new FormData();
    const rawFile = document.getElementById('rawDisplayFile').files[0];
    const reportFile = document.getElementById('reportWeekFile').files[0];
    const weekNum = document.getElementById('weekNumber').value;

    if (!rawFile || !reportFile) {
        showNotification('Please select both files', 'error');
        return;
    }

    formData.append('raw_file', rawFile);
    formData.append('report_file', reportFile);
    formData.append('week_num', weekNum);

    try {
        showUploadProgress(true);
        updateUploadStatus('Uploading files...');

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            currentSessionId = result.session_id;
            updateUploadStatus('Files uploaded successfully!');
            showNotification('Files uploaded successfully! You can now process the data.', 'success');

            // Enable process button
            enableProcessButton();

            // Store session info
            document.getElementById('sessionId').value = currentSessionId;
            document.getElementById('processWeekNum').value = weekNum;

        } else {
            throw new Error(result.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(error.message, 'error');
        updateUploadStatus('Upload failed');
    } finally {
        hideUploadProgress();
    }
}

async function startProcessing() {
    if (!currentSessionId) {
        showNotification('Please upload files first', 'error');
        return;
    }

    const weekNum = document.getElementById('processWeekNum').value || document.getElementById('weekNumber').value;

    try {
        setProcessingState(true);
        updateProcessStatus('Starting data processing...');

        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                week_num: weekNum
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            currentJobId = result.job_id;
            updateProcessStatus('Processing started...');
            startStatusPolling();
        } else {
            throw new Error(result.error || 'Processing failed to start');
        }
    } catch (error) {
        console.error('Processing error:', error);
        showNotification(error.message, 'error');
        setProcessingState(false);
        updateProcessStatus('Processing failed');
    }
}

function startStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentJobId}`);
            const status = await response.json();

            if (response.ok) {
                updateProgress(status.progress || 0);
                updateProcessStatus(getStatusMessage(status.status, status.progress));

                if (status.status === 'completed') {
                    clearInterval(statusCheckInterval);
                    handleProcessingComplete(status.result);
                } else if (status.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    handleProcessingError(status.error);
                }
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }, 2000); // Check every 2 seconds
}

function handleProcessingComplete(result) {
    setProcessingState(false);
    updateProcessStatus('Processing completed successfully!');
    updateProgress(100);

    // Show results
    showResults(result);
    showNotification('Data processing completed successfully!', 'success');

    // Reset for next processing
    setTimeout(() => {
        resetProgressBar();
    }, 3000);
}

function handleProcessingError(error) {
    setProcessingState(false);
    updateProcessStatus('Processing failed');
    showNotification(`Processing failed: ${error}`, 'error');
    resetProgressBar();
}

function showResults(result) {
    // Update statistics
    updateStatistics(result.summary);

    // Show charts
    updateCharts(result.charts);

    // Update download links
    updateDownloadLinks(result);

    // Show result sections
    showSection('dashboardSection');
    showSection('downloadSection');

    // If there are alerts, show them
    if (result.all_changes && result.all_changes.length > 0) {
        displayAlerts(result.all_changes);
        showSection('alertsSection');
    }
}

function updateStatistics(summary) {
    const totalModels = summary.models_increased + summary.models_decreased + (summary.models_unchanged || 0);

    document.getElementById('totalModels').textContent = totalModels;
    document.getElementById('modelsIncreased').textContent = summary.models_increased;
    document.getElementById('modelsDecreased').textContent = summary.models_decreased;
    document.getElementById('modelsUnchanged').textContent = summary.models_unchanged || 0;
}

function updateCharts(charts) {
    console.log('Updating charts:', charts);

    if (charts.increases) {
        const increasesImg = document.getElementById('increasesChart');
        const increasesPlaceholder = document.getElementById('increasesPlaceholder');

        increasesImg.src = `/charts/increases/${charts.increases}`;
        increasesImg.classList.remove('hidden');
        if (increasesPlaceholder) increasesPlaceholder.style.display = 'none';
        console.log('Set increases chart src:', increasesImg.src);
    } else {
        console.log('No increases chart data');
    }

    if (charts.decreases) {
        const decreasesImg = document.getElementById('decreasesChart');
        const decreasesPlaceholder = document.getElementById('decreasesPlaceholder');

        decreasesImg.src = `/charts/decreases/${charts.decreases}`;
        decreasesImg.classList.remove('hidden');
        if (decreasesPlaceholder) decreasesPlaceholder.style.display = 'none';
        console.log('Set decreases chart src:', decreasesImg.src);
    } else {
        console.log('No decreases chart data');
    }
}

function updateDownloadLinks(result) {
    const reportLink = document.getElementById('downloadReportLink');
    const alertsLink = document.getElementById('downloadAlertsLink');

    if (reportLink && result.report_file) {
        reportLink.href = `/download/${result.report_file}`;
        reportLink.download = result.report_file;
        reportLink.classList.remove('disabled');
    }

    if (alertsLink && result.alert_file) {
        alertsLink.href = `/download/${result.alert_file}`;
        alertsLink.download = result.alert_file;
        alertsLink.classList.remove('disabled');
    }

    // Add chart download links
    const chartDownloads = document.getElementById('chartDownloads');
    if (chartDownloads && result.charts) {
        chartDownloads.innerHTML = '';

        Object.entries(result.charts).forEach(([type, path]) => {
            if (path) {
                const filename = path.split('/').pop();
                const downloadItem = document.createElement('div');
                downloadItem.className = 'chart-download-item';
                downloadItem.innerHTML = `
                    <span>${type.charAt(0).toUpperCase() + type.slice(1)} Chart</span>
                    <a href="/download/${filename}" download="${filename}" class="btn btn--sm btn--secondary">
                        Download PNG
                    </a>
                `;
                chartDownloads.appendChild(downloadItem);
            }
        });
    }
}

function displayAlerts(alerts) {
    const tableBody = document.getElementById('alertsTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    alerts.forEach(alert => {
        const row = document.createElement('tr');
        const changeClass = alert.Difference > 0 ? 'increase' : 'decrease';
        const statusText = alert.Change_Type || (alert.Difference > 0 ? 'Increase' : 'Decrease');

        row.innerHTML = `
            <td>${alert.Model}</td>
            <td>${alert.Previous}</td>
            <td>${alert.Current}</td>
            <td class="${changeClass}">${alert.Difference > 0 ? '+' : ''}${alert.Difference}</td>
            <td><span class="status-badge status-${changeClass}">${statusText}</span></td>
        `;

        tableBody.appendChild(row);
    });
}

// Utility functions
function updateFileStatus(statusId, file) {
    const statusEl = document.getElementById(statusId);
    if (statusEl && file) {
        statusEl.innerHTML = `
            <span class="file-name">✓ ${file.name}</span>
            <span class="file-size">(${formatFileSize(file.size)})</span>
        `;
        statusEl.classList.add('file-selected');
    }
}

function checkUploadReadiness() {
    const uploadBtn = document.getElementById('uploadBtn');
    const canUpload = uploadedFiles.raw && uploadedFiles.report;

    if (uploadBtn) {
        uploadBtn.disabled = !canUpload;
    }
}

function enableProcessButton() {
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.disabled = false;
    }
}

function setProcessingState(processing) {
    const processBtn = document.getElementById('processBtn');
    const processText = document.getElementById('processText');
    const loadingSpinner = document.getElementById('loadingSpinner');

    if (processBtn) {
        processBtn.disabled = processing;
        if (processing) {
            processBtn.classList.add('loading');
        } else {
            processBtn.classList.remove('loading');
        }
    }

    if (processText) {
        processText.textContent = processing ? 'Processing...' : 'Process Data';
    }

    if (loadingSpinner) {
        loadingSpinner.classList.toggle('hidden', !processing);
    }
}

function updateProgress(percentage) {
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (progressBar && percentage > 0) {
        progressBar.classList.remove('hidden');
    }

    if (progressFill) {
        progressFill.style.width = `${percentage}%`;
    }

    if (progressText) {
        progressText.textContent = `${Math.round(percentage)}%`;
    }
}

function resetProgressBar() {
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (progressBar) {
        progressBar.classList.add('hidden');
    }

    if (progressFill) {
        progressFill.style.width = '0%';
    }

    if (progressText) {
        progressText.textContent = '0%';
    }
}

function updateProcessStatus(message) {
    const statusEl = document.getElementById('processStatus');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

function showUploadProgress(show) {
    const progressEl = document.getElementById('uploadProgress');
    if (progressEl) {
        progressEl.classList.toggle('hidden', !show);
    }
}

function hideUploadProgress() {
    showUploadProgress(false);
}

function updateUploadStatus(message) {
    const statusEl = document.getElementById('uploadStatus');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.remove('hidden');
        section.classList.add('fade-in');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.textContent = message;

    // Find or create flash messages container
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        const header = document.querySelector('.header');
        if (header) {
            header.insertAdjacentElement('afterend', container);
        } else {
            document.querySelector('.container').prepend(container);
        }
    }

    container.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
        if (container.children.length === 0) {
            container.remove();
        }
    }, 5000);
}

function getStatusMessage(status, progress) {
    switch (status) {
        case 'started':
            return 'Initializing processing...';
        case 'processing':
            if (progress < 30) return 'Loading and validating data...';
            if (progress < 70) return 'Processing changes and generating reports...';
            return 'Generating charts and finalizing...';
        case 'completed':
            return 'Processing completed successfully!';
        case 'failed':
            return 'Processing failed';
        default:
            return 'Processing...';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function filterAlerts() {
    const filterValue = document.getElementById('alertFilter')?.value || 'all';
    const searchValue = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const tableBody = document.getElementById('alertsTableBody');

    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr');

    rows.forEach(row => {
        const model = row.cells[0].textContent.toLowerCase();
        const change = parseInt(row.cells[3].textContent);

        let showRow = true;

        // Filter by type
        if (filterValue === 'increases' && change <= 0) showRow = false;
        if (filterValue === 'decreases' && change >= 0) showRow = false;

        // Filter by search
        if (searchValue && !model.includes(searchValue)) showRow = false;

        row.style.display = showRow ? '' : 'none';
    });
}

function exportAlerts() {
    const tableBody = document.getElementById('alertsTableBody');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('tr:not([style*="display: none"])'));
    const data = rows.map(row => {
        return {
            Model: row.cells[0].textContent,
            Previous: parseInt(row.cells[1].textContent),
            Current: parseInt(row.cells[2].textContent),
            Change: parseInt(row.cells[3].textContent),
            Status: row.cells[4].textContent
        };
    });

    const csv = convertToCSV(data);
    downloadCSV(csv, 'filtered_alerts.csv');
}

function convertToCSV(data) {
    if (!data.length) return '';

    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
    ].join('\n');

    return csvContent;
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function checkExistingSession() {
    // Check if there's an existing session (useful for page refreshes)
    const sessionId = document.getElementById('sessionId')?.value;
    if (sessionId) {
        currentSessionId = sessionId;
        enableProcessButton();
    }
}