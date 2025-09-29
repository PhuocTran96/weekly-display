// Upload Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeUploadPage();
});

function initializeUploadPage() {
    const uploadForm = document.getElementById('uploadForm');
    const rawFile = document.getElementById('rawDisplayFile');
    const reportFile = document.getElementById('reportWeekFile');
    const uploadBtn = document.getElementById('uploadBtn');

    // File change listeners
    if (rawFile) {
        rawFile.addEventListener('change', function(e) {
            updateFileStatus('rawDisplayStatus', e.target.files[0]);
            checkFormValidity();
        });
    }

    if (reportFile) {
        reportFile.addEventListener('change', function(e) {
            updateFileStatus('reportWeekStatus', e.target.files[0]);
            checkFormValidity();
        });
    }

    // Form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }

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

    function checkFormValidity() {
        const hasRawFile = rawFile && rawFile.files.length > 0;
        const hasReportFile = reportFile && reportFile.files.length > 0;

        if (uploadBtn) {
            uploadBtn.disabled = !(hasRawFile && hasReportFile);
        }
    }

    function handleFormSubmit(e) {
        e.preventDefault();

        const uploadText = document.getElementById('uploadText');
        const uploadSpinner = document.getElementById('uploadSpinner');

        // Show loading state
        if (uploadBtn) uploadBtn.disabled = true;
        if (uploadText) uploadText.textContent = 'Uploading...';
        if (uploadSpinner) uploadSpinner.classList.remove('hidden');

        // Show progress
        showUploadProgress();

        // Submit form normally (let Flask handle it)
        e.target.submit();
    }

    function showUploadProgress() {
        const progressEl = document.getElementById('uploadProgress');
        if (progressEl) {
            progressEl.classList.remove('hidden');

            // Simulate progress
            let progress = 0;
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const uploadStatus = document.getElementById('uploadStatus');

            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;

                if (progressFill) progressFill.style.width = `${progress}%`;
                if (progressText) progressText.textContent = `${Math.round(progress)}%`;

                if (progress >= 90) {
                    clearInterval(interval);
                    if (uploadStatus) uploadStatus.textContent = 'Processing files...';
                }
            }, 200);
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}