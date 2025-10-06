/**
 * Email Module - Handles email notifications
 */

export class EmailManager {
    constructor() {
        this.previewData = null;
        this.selectedRecipients = new Set();
        this.resendMode = false;
        this.resendJobId = null;
        this.initializeEventListeners();
    }

    init() {
        // Public init method for external initialization
        console.log('EmailManager initialized');
    }

    initializeEventListeners() {
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        if (sendEmailBtn) {
            sendEmailBtn.addEventListener('click', () => this.showEmailPreview());
        }

        // Modal event listeners
        this.initializeModalListeners();
    }

    initializeModalListeners() {
        // Close modal
        const closeBtn = document.getElementById('closeEmailModal');
        const cancelBtn = document.getElementById('cancelEmailSend');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePreviewModal());
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closePreviewModal());
        }

        // Select/Deselect All
        const selectAllBtn = document.getElementById('selectAllRecipients');
        const deselectAllBtn = document.getElementById('deselectAllRecipients');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllRecipients());
        }
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAllRecipients());
        }

        // Type Filter
        const typeFilter = document.getElementById('recipientTypeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => this.filterRecipients(e.target.value));
        }

        // Send Selected Emails
        const sendSelectedBtn = document.getElementById('sendSelectedEmails');
        if (sendSelectedBtn) {
            sendSelectedBtn.addEventListener('click', () => this.sendSelectedEmails());
        }

        // Preview Tabs
        const tabButtons = document.querySelectorAll('.preview-tab');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchPreviewTab(e.target.dataset.tab));
        });

        // Close modal on outside click
        const modal = document.getElementById('emailPreviewModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closePreviewModal();
                }
            });
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

    async showEmailPreview(weekNum = null) {
        console.log('Email preview button clicked');

        // If week number is not provided as parameter, try to get it from the page
        if (!weekNum) {
            weekNum = this.getWeekNum();
            console.log('Week number detected from page:', weekNum);
        } else {
            console.log('Week number provided as parameter:', weekNum);
        }

        if (!weekNum) {
            console.error('Week number not found');
            this.showNotification('Week number not found. Please ensure you have processed data.', 'error');
            return;
        }

        // Show modal
        const modal = document.getElementById('emailPreviewModal');
        const loading = document.getElementById('previewLoading');
        const content = document.getElementById('previewContent');
        const error = document.getElementById('previewError');

        console.log('Modal element:', modal ? 'Found' : 'Not found');

        // Check if modal exists (only on results page)
        if (!modal) {
            console.log('Email preview modal not available on this page');
            this.showNotification('Email preview is only available on the results page.', 'warning');
            return;
        }

        modal.style.display = 'flex';
        loading.style.display = 'block';
        content.style.display = 'none';
        error.style.display = 'none';

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        try {
            // Fetch preview data
            const response = await fetch('/process/preview-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ week_num: weekNum })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.previewData = result;
                this.displayPreview(result);
                loading.style.display = 'none';
                content.style.display = 'block';
            } else {
                throw new Error(result.error || 'Failed to load email preview');
            }

        } catch (error) {
            console.error('Email preview error:', error);
            loading.style.display = 'none';
            error.style.display = 'block';
            document.getElementById('previewErrorMessage').textContent = error.message;
        }
    }

    displayPreview(data) {
        // Set week number
        document.getElementById('modalWeekNum').textContent = data.week_num;

        // Show helpful message if no recipients
        if (data.message && data.total_recipients === 0) {
            this.showNotification(data.message, 'warning');
        }

        // Display recipients
        this.displayRecipients(data.recipients);

        // Display email previews
        if (data.pic_preview) {
            document.getElementById('picSubject').textContent = data.pic_preview.subject;
            document.getElementById('picBody').innerHTML = data.pic_preview.body_html;
        } else {
            document.getElementById('picSubject').textContent = 'No PIC email preview available';
            document.getElementById('picBody').innerHTML = '<p style="color: #666;">No PIC recipients found. PICs will be notified when you reprocess data with the updated system.</p>';
        }

        if (data.boss_preview) {
            document.getElementById('bossSubject').textContent = data.boss_preview.subject;
            document.getElementById('bossBody').innerHTML = data.boss_preview.body_html;
        } else {
            document.getElementById('bossSubject').textContent = 'No Boss email preview available';
            document.getElementById('bossBody').innerHTML = '<p style="color: #666;">No boss recipients configured. Set BOSS_EMAILS in your .env file to enable boss notifications.</p>';
        }

        // Update counts
        this.updateRecipientCounts();
    }

    displayRecipients(recipients) {
        const recipientList = document.getElementById('recipientList');
        recipientList.innerHTML = '';

        const allRecipients = [...recipients.pics, ...recipients.bosses];

        allRecipients.forEach(recipient => {
            const recipientCard = document.createElement('div');
            recipientCard.className = `recipient-card recipient-${recipient.type.toLowerCase()}`;
            recipientCard.dataset.recipientId = recipient.id;
            recipientCard.dataset.recipientType = recipient.type.toLowerCase();

            let detailsHtml = '';
            if (recipient.type === 'PIC') {
                detailsHtml = `
                    <div class="recipient-details">
                        <div>Stores: ${recipient.store_count}</div>
                        <div>Decreases: ${recipient.decrease_count}</div>
                    </div>
                `;
            } else {
                detailsHtml = `
                    <div class="recipient-details">
                        <div>Stores Affected: ${recipient.stores_affected}</div>
                        <div>Total Decreases: ${recipient.total_decreases}</div>
                    </div>
                `;
            }

            recipientCard.innerHTML = `
                <div class="recipient-checkbox">
                    <input type="checkbox" id="recipient-${recipient.id}" value="${recipient.id}">
                </div>
                <div class="recipient-info">
                    <div class="recipient-header">
                        <label for="recipient-${recipient.id}">
                            <strong>${recipient.name}</strong>
                            <span class="recipient-type-badge">${recipient.type}</span>
                        </label>
                    </div>
                    <div class="recipient-email">${recipient.email}</div>
                    ${detailsHtml}
                </div>
            `;

            recipientList.appendChild(recipientCard);

            // Add change listener
            const checkbox = recipientCard.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedRecipients.add(recipient.id);
                } else {
                    this.selectedRecipients.delete(recipient.id);
                }
                this.updateRecipientCounts();
            });
        });
    }

    selectAllRecipients() {
        const checkboxes = document.querySelectorAll('#recipientList input[type="checkbox"]:not([style*="display: none"])');
        checkboxes.forEach(cb => {
            cb.checked = true;
            this.selectedRecipients.add(cb.value);
        });
        this.updateRecipientCounts();
    }

    deselectAllRecipients() {
        const checkboxes = document.querySelectorAll('#recipientList input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = false;
        });
        this.selectedRecipients.clear();
        this.updateRecipientCounts();
    }

    filterRecipients(filterType) {
        const recipientCards = document.querySelectorAll('.recipient-card');

        recipientCards.forEach(card => {
            const cardType = card.dataset.recipientType;

            if (filterType === 'all' || cardType === filterType) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });

        this.updateRecipientCounts();
    }

    updateRecipientCounts() {
        const selectedCount = this.selectedRecipients.size;
        const totalCount = this.previewData?.total_recipients || 0;

        document.getElementById('selectedCount').textContent = selectedCount;
        document.getElementById('totalCount').textContent = totalCount;

        // Enable/disable send button
        const sendBtn = document.getElementById('sendSelectedEmails');
        if (sendBtn) {
            sendBtn.disabled = selectedCount === 0;
        }
    }

    async sendSelectedEmails() {
        if (this.selectedRecipients.size === 0) {
            this.showNotification('Please select at least one recipient', 'warning');
            return;
        }

        const weekNum = this.getWeekNum();
        const sendBtn = document.getElementById('sendSelectedEmails');
        const originalText = sendBtn.textContent;

        try {
            // Disable button and show loading
            sendBtn.disabled = true;
            document.getElementById('sendBtnText').textContent = 'Sending...';
            document.getElementById('sendLoadingSpinner').classList.remove('hidden');

            const selectedArray = Array.from(this.selectedRecipients);

            let endpoint, body;

            // Check if we're in resend mode (from history page)
            if (this.resendMode && this.resendJobId) {
                endpoint = `/api/history/${this.resendJobId}/resend-emails`;
                body = {
                    selected_recipients: selectedArray
                };
            } else {
                // Normal send mode (from dashboard)
                endpoint = '/process/send-selective-emails';
                body = {
                    week_num: weekNum,
                    selected_recipients: selectedArray
                };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification(result.message || `Emails sent successfully! Sent: ${result.emails_sent || selectedArray.length}`, 'success');
                this.closePreviewModal();

                // Reset resend mode
                this.resendMode = false;
                this.resendJobId = null;

                // Show detailed results if there were any errors
                if (result.errors && result.errors.length > 0) {
                    console.warn('Some emails failed:', result.errors);
                }
            } else {
                throw new Error(result.error || 'Failed to send emails');
            }

        } catch (error) {
            console.error('Email sending error:', error);
            this.showNotification(error.message, 'error');
        } finally {
            // Re-enable button
            sendBtn.disabled = false;
            document.getElementById('sendBtnText').textContent = originalText;
            document.getElementById('sendLoadingSpinner').classList.add('hidden');
        }
    }

    switchPreviewTab(tabId) {
        // Update tab buttons
        const tabButtons = document.querySelectorAll('.preview-tab');
        tabButtons.forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update panels
        const panels = document.querySelectorAll('.preview-panel');
        panels.forEach(panel => {
            if (panel.id === tabId) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }

    closePreviewModal() {
        const modal = document.getElementById('emailPreviewModal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Reset state
        this.selectedRecipients.clear();
        this.previewData = null;
    }

    getWeekNum() {
        return document.getElementById('weekNumber')?.value ||
               document.getElementById('processWeekNum')?.value ||
               this.getWeekFromResults();
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