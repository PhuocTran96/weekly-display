/**
 * Upload Module - Handles file uploads
 */

export class UploadManager {
    constructor() {
        this.uploadedFiles = { raw: null, report: null };
        this.currentSessionId = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => this.handleFileUpload(e));
        }

        const rawDisplayFile = document.getElementById('rawDisplayFile');
        const reportWeekFile = document.getElementById('reportWeekFile');

        if (rawDisplayFile) {
            rawDisplayFile.addEventListener('change', (e) => {
                this.updateFileStatus('rawDisplayStatus', e.target.files[0]);
                this.uploadedFiles.raw = e.target.files[0];
                this.checkUploadReadiness();
            });
        }

        if (reportWeekFile) {
            reportWeekFile.addEventListener('change', (e) => {
                this.updateFileStatus('reportWeekStatus', e.target.files[0]);
                this.uploadedFiles.report = e.target.files[0];
                this.checkUploadReadiness();
            });
        }
    }

    async handleFileUpload(e) {
        e.preventDefault();

        const formData = new FormData();
        const rawFile = document.getElementById('rawDisplayFile').files[0];
        const reportFile = document.getElementById('reportWeekFile').files[0];
        const weekNum = document.getElementById('weekNumber').value;

        if (!rawFile || !reportFile) {
            this.showNotification('Please select both files', 'error');
            return;
        }

        formData.append('raw_file', rawFile);
        formData.append('report_file', reportFile);
        formData.append('week_num', weekNum);

        try {
            this.showUploadProgress(true);
            this.updateUploadStatus('Uploading files...');

            const response = await fetch('/upload/', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.currentSessionId = result.session_id;
                this.updateUploadStatus('Files uploaded successfully!');
                this.showNotification('Files uploaded successfully! You can now process the data.', 'success');
                this.enableProcessButton();

                document.getElementById('sessionId').value = this.currentSessionId;
                document.getElementById('processWeekNum').value = weekNum;
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification(error.message, 'error');
            this.updateUploadStatus('Upload failed');
        } finally {
            this.showUploadProgress(false);
        }
    }

    updateFileStatus(statusId, file) {
        const statusEl = document.getElementById(statusId);
        if (statusEl && file) {
            statusEl.innerHTML = `
                <span class="file-name">✓ ${file.name}</span>
                <span class="file-size">(${this.formatFileSize(file.size)})</span>
            `;
            statusEl.classList.add('file-selected');
        }
    }

    checkUploadReadiness() {
        const uploadBtn = document.getElementById('uploadBtn');
        const canUpload = this.uploadedFiles.raw && this.uploadedFiles.report;
        if (uploadBtn) {
            uploadBtn.disabled = !canUpload;
        }
    }

    enableProcessButton() {
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = false;
        }
    }

    showUploadProgress(show) {
        const progressEl = document.getElementById('uploadProgress');
        if (progressEl) {
            progressEl.classList.toggle('hidden', !show);
        }
    }

    updateUploadStatus(message) {
        const statusEl = document.getElementById('uploadStatus');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `flash-message flash-${type}`;
        notification.textContent = message;

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

        setTimeout(() => {
            notification.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        }, 5000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getSessionId() {
        return this.currentSessionId;
    }
}