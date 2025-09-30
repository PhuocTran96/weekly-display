/**
 * Main Application Entry Point
 * Modern ES6 module-based architecture
 */

import { UploadManager } from './modules/upload.module.js';
import { ProcessManager } from './modules/processor.module.js';
import { ResultsManager } from './modules/results.module.js';
import { EmailManager } from './modules/email.module.js';

class WeeklyDisplayApp {
    constructor() {
        this.uploadManager = null;
        this.processManager = null;
        this.resultsManager = null;
        this.emailManager = null;
    }

    async initialize() {
        console.log('Initializing Weekly Display Tracking Application...');

        try {
            // Initialize managers
            this.uploadManager = new UploadManager();
            this.processManager = new ProcessManager(this.uploadManager);
            this.resultsManager = new ResultsManager();
            this.emailManager = new EmailManager();

            // Setup drag and drop
            this.setupDragAndDrop();

            // Check for existing session
            this.checkExistingSession();

            console.log('Application initialized successfully');
        } catch (error) {
            console.error('Application initialization error:', error);
        }
    }

    setupDragAndDrop() {
        const uploadAreas = document.querySelectorAll('.upload-area');

        uploadAreas.forEach(area => {
            const fileInput = area.querySelector('.file-input');
            if (!fileInput) return;

            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('drag-over');
            });

            area.addEventListener('dragleave', (e) => {
                e.preventDefault();
                area.classList.remove('drag-over');
            });

            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const file = files[0];
                    if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
                        fileInput.files = files;
                        fileInput.dispatchEvent(new Event('change'));
                    } else {
                        this.uploadManager.showNotification('Please select a CSV file', 'error');
                    }
                }
            });
        });
    }

    checkExistingSession() {
        const sessionId = document.getElementById('sessionId')?.value;
        if (sessionId) {
            this.uploadManager.currentSessionId = sessionId;
            this.uploadManager.enableProcessButton();
        }
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new WeeklyDisplayApp();
    app.initialize();
});