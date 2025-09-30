/**
 * Processor Module - Handles data processing
 */

export class ProcessManager {
    constructor(uploadManager) {
        this.uploadManager = uploadManager;
        this.currentJobId = null;
        this.statusCheckInterval = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.startProcessing());
        }
    }

    async startProcessing() {
        const sessionId = this.uploadManager.getSessionId();

        if (!sessionId) {
            this.showNotification('Please upload files first', 'error');
            return;
        }

        const weekNum = document.getElementById('processWeekNum').value ||
                       document.getElementById('weekNumber').value;

        try {
            this.setProcessingState(true);
            this.updateProcessStatus('Starting data processing...');

            const response = await fetch('/process/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    week_num: weekNum
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.currentJobId = result.job_id;
                this.updateProcessStatus('Processing started...');
                this.startStatusPolling();
            } else {
                throw new Error(result.error || 'Processing failed to start');
            }
        } catch (error) {
            console.error('Processing error:', error);
            this.showNotification(error.message, 'error');
            this.setProcessingState(false);
            this.updateProcessStatus('Processing failed');
        }
    }

    startStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }

        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/process/status/${this.currentJobId}`);
                const status = await response.json();

                if (response.ok) {
                    this.updateProgress(status.progress || 0);
                    this.updateProcessStatus(this.getStatusMessage(status.status, status.progress));

                    if (status.status === 'completed') {
                        clearInterval(this.statusCheckInterval);
                        this.handleProcessingComplete(status.result);
                    } else if (status.status === 'failed') {
                        clearInterval(this.statusCheckInterval);
                        this.handleProcessingError(status.error);
                    }
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 2000);
    }

    handleProcessingComplete(result) {
        this.setProcessingState(false);
        this.updateProcessStatus('Processing completed successfully!');
        this.updateProgress(100);

        // Import and use results manager
        import('./results.module.js').then(module => {
            const resultsManager = new module.ResultsManager();
            resultsManager.showResults(result);
        });

        this.showNotification('Data processing completed successfully!', 'success');

        setTimeout(() => {
            this.resetProgressBar();
        }, 3000);
    }

    handleProcessingError(error) {
        this.setProcessingState(false);
        this.updateProcessStatus('Processing failed');
        this.showNotification(`Processing failed: ${error}`, 'error');
        this.resetProgressBar();
    }

    setProcessingState(processing) {
        const processBtn = document.getElementById('processBtn');
        const processText = document.getElementById('processText');

        if (processBtn) {
            processBtn.disabled = processing;
            processBtn.classList.toggle('loading', processing);
        }

        if (processText) {
            processText.textContent = processing ? 'Processing...' : 'Process Data';
        }
    }

    updateProgress(percentage) {
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

    resetProgressBar() {
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        if (progressBar) progressBar.classList.add('hidden');
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = '0%';
    }

    updateProcessStatus(message) {
        const statusEl = document.getElementById('processStatus');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }

    getStatusMessage(status, progress) {
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

    showNotification(message, type) {
        // Reuse notification from upload manager
        this.uploadManager.showNotification(message, type);
    }
}