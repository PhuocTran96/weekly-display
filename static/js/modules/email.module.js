/**
 * Email Module - Handles email notifications
 */

export class EmailManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        if (sendEmailBtn) {
            sendEmailBtn.addEventListener('click', () => this.sendEmails());
        }
    }

    async sendEmails() {
        const weekNum = document.getElementById('weekNumber')?.value ||
                       document.getElementById('processWeekNum')?.value ||
                       this.getWeekFromResults();

        if (!weekNum) {
            this.showNotification('Week number not found', 'error');
            return;
        }

        const sendEmailBtn = document.getElementById('sendEmailBtn');
        const originalText = sendEmailBtn?.textContent;

        try {
            // Disable button and show loading
            if (sendEmailBtn) {
                sendEmailBtn.disabled = true;
                sendEmailBtn.textContent = 'Sending Emails...';
            }

            this.showNotification('Sending email notifications...', 'info');

            const response = await fetch('/process/send-emails', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ week_num: weekNum })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification(
                    result.message || `Successfully sent ${result.emails_sent} email(s)`,
                    'success'
                );

                // Show any partial errors
                if (result.errors && result.errors.length > 0) {
                    console.warn('Email sending had some errors:', result.errors);
                }
            } else {
                throw new Error(result.error || 'Failed to send emails');
            }

        } catch (error) {
            console.error('Email sending error:', error);
            this.showNotification(error.message, 'error');
        } finally {
            // Re-enable button
            if (sendEmailBtn) {
                sendEmailBtn.disabled = false;
                sendEmailBtn.textContent = originalText || 'Send Email Notifications';
            }
        }
    }

    getWeekFromResults() {
        // Try to extract week number from hidden input
        const processWeekNum = document.getElementById('processWeekNum');
        if (processWeekNum && processWeekNum.value) {
            return processWeekNum.value;
        }

        // Try to extract from page content
        const weekNumEl = document.querySelector('[data-week-num]');
        if (weekNumEl) {
            return weekNumEl.getAttribute('data-week-num');
        }

        // Try to get from alert file name in downloads
        const alertLink = document.getElementById('downloadAlertsLink');
        if (alertLink) {
            const href = alertLink.getAttribute('href');
            const match = href.match(/week-(\d+)/);
            if (match) {
                return match[1];
            }
        }

        return null;
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
                document.querySelector('.container')?.prepend(container);
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
}