/**
 * History Manager Module
 * Manages processing job history display and interactions
 */

export class HistoryManager {
    constructor() {
        this.currentPage = 1;
        this.pageLimit = 10;
        this.totalPages = 1;
        this.filters = {
            week: null,
            status: null
        };
    }

    /**
     * Initialize the history manager
     */
    init() {
        console.log('Initializing History Manager...');
        this.loadStats();
        this.loadHistory();
    }

    /**
     * Load statistics summary
     */
    async loadStats() {
        try {
            const response = await fetch('/api/history/stats');
            const data = await response.json();

            if (data.success) {
                document.getElementById('totalJobs').textContent = data.stats.total_jobs;
                document.getElementById('successfulJobs').textContent = data.stats.successful_jobs;
                document.getElementById('failedJobs').textContent = data.stats.failed_jobs;
                document.getElementById('weeksProcessed').textContent = data.stats.weeks_processed;
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    /**
     * Load job history with current filters and pagination
     */
    async loadHistory() {
        try {
            const container = document.getElementById('jobsTableContainer');
            container.innerHTML = '<div class="loading"><p>Loading history...</p></div>';

            // Build query params
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageLimit
            });

            if (this.filters.week) {
                params.append('week', this.filters.week);
            }

            const response = await fetch(`/api/history/?${params}`);
            const data = await response.json();

            if (data.success) {
                this.renderJobsTable(data.jobs);
                this.updatePagination(data.pagination);
            } else {
                container.innerHTML = `<div class="empty-state">
                    <div class="empty-state-icon">❌</div>
                    <h3>Error Loading History</h3>
                    <p>${data.error}</p>
                </div>`;
            }
        } catch (error) {
            console.error('Error loading history:', error);
            const container = document.getElementById('jobsTableContainer');
            container.innerHTML = `<div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <h3>Error Loading History</h3>
                <p>${error.message}</p>
            </div>`;
        }
    }

    /**
     * Render jobs table
     */
    renderJobsTable(jobs) {
        const container = document.getElementById('jobsTableContainer');

        if (jobs.length === 0) {
            container.innerHTML = `<div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>No Processing Jobs Found</h3>
                <p>Process some data to see the history here.</p>
            </div>`;
            return;
        }

        // Filter by status if needed
        let filteredJobs = jobs;
        if (this.filters.status) {
            filteredJobs = jobs.filter(job => job.status === this.filters.status);
        }

        const tableHTML = `
            <div class="jobs-table">
                <table>
                    <thead>
                        <tr>
                            <th>Week</th>
                            <th>Date</th>
                            <th>Status</th>
                            <th>Models Increased</th>
                            <th>Models Decreased</th>
                            <th>Stores Affected</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${filteredJobs.map(job => this.renderJobRow(job)).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = tableHTML;
    }

    /**
     * Render single job row
     */
    renderJobRow(job) {
        const date = new Date(job.timestamp);
        const dateStr = date.toLocaleString();

        const statusClass = job.status === 'completed' ? 'status-completed' :
                           job.status === 'failed' ? 'status-failed' : 'status-processing';

        const statusText = job.status.charAt(0).toUpperCase() + job.status.slice(1);

        const summary = job.summary || {};

        return `
            <tr>
                <td><strong>Week ${job.week_num}</strong></td>
                <td>${dateStr}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${summary.models_increased || 0}</td>
                <td>${summary.models_decreased || 0}</td>
                <td>${summary.stores_affected || 0}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action btn-view" onclick="window.historyManager.viewJobDetails('${job.job_id}')">
                            👁️ View
                        </button>
                        ${job.status === 'completed' ? `
                            <button class="btn-action btn-resend" onclick="window.historyManager.resendEmails('${job.job_id}', ${job.week_num})">
                                📧 Resend
                            </button>
                        ` : ''}
                        <button class="btn-action btn-delete" onclick="window.historyManager.deleteJob('${job.job_id}')">
                            🗑️ Delete
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Update pagination controls
     */
    updatePagination(pagination) {
        this.currentPage = pagination.page;
        this.totalPages = pagination.total_pages;

        const paginationDiv = document.getElementById('pagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (this.totalPages > 1) {
            paginationDiv.style.display = 'flex';
            pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
            prevBtn.disabled = this.currentPage === 1;
            nextBtn.disabled = this.currentPage === this.totalPages;
        } else {
            paginationDiv.style.display = 'none';
        }
    }

    /**
     * Go to previous page
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadHistory();
        }
    }

    /**
     * Go to next page
     */
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadHistory();
        }
    }

    /**
     * Apply filters
     */
    applyFilters() {
        const weekInput = document.getElementById('weekFilter').value;
        const statusSelect = document.getElementById('statusFilter').value;

        this.filters.week = weekInput ? parseInt(weekInput) : null;
        this.filters.status = statusSelect || null;

        this.currentPage = 1; // Reset to first page
        this.loadHistory();
    }

    /**
     * Clear filters
     */
    clearFilters() {
        document.getElementById('weekFilter').value = '';
        document.getElementById('statusFilter').value = '';

        this.filters.week = null;
        this.filters.status = null;

        this.currentPage = 1;
        this.loadHistory();
    }

    /**
     * View job details in modal
     */
    async viewJobDetails(jobId) {
        try {
            const response = await fetch(`/api/history/${jobId}`);
            const data = await response.json();

            if (data.success) {
                this.showJobDetailsModal(data.job);
            } else {
                alert(`Error loading job details: ${data.error}`);
            }
        } catch (error) {
            console.error('Error loading job details:', error);
            alert(`Error loading job details: ${error.message}`);
        }
    }

    /**
     * Show job details modal
     */
    showJobDetailsModal(job) {
        const modal = document.getElementById('jobDetailsModal');
        const body = document.getElementById('jobDetailsBody');

        const date = new Date(job.timestamp);
        const summary = job.summary || {};
        const files = job.files || {};
        const charts = job.charts || {};

        body.innerHTML = `
            <div class="detail-section">
                <h3>Basic Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Job ID</label>
                        <value>${job.job_id}</value>
                    </div>
                    <div class="detail-item">
                        <label>Week Number</label>
                        <value>Week ${job.week_num}</value>
                    </div>
                    <div class="detail-item">
                        <label>Status</label>
                        <value><span class="status-badge status-${job.status}">${job.status}</span></value>
                    </div>
                    <div class="detail-item">
                        <label>Processing Date</label>
                        <value>${date.toLocaleString()}</value>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h3>Summary Statistics</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Models Increased</label>
                        <value>${summary.models_increased || 0}</value>
                    </div>
                    <div class="detail-item">
                        <label>Models Decreased</label>
                        <value>${summary.models_decreased || 0}</value>
                    </div>
                    <div class="detail-item">
                        <label>Stores Affected</label>
                        <value>${summary.stores_affected || 0}</value>
                    </div>
                    <div class="detail-item">
                        <label>Total Decreases</label>
                        <value>${summary.total_decreases || 0}</value>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h3>Generated Files</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Report File</label>
                        <value>${this.renderFileLink(job.job_id, 'report', files.report_file)}</value>
                    </div>
                    <div class="detail-item">
                        <label>Alert File</label>
                        <value>${this.renderFileLink(job.job_id, 'alert', files.alert_file)}</value>
                    </div>
                    <div class="detail-item">
                        <label>Increases File</label>
                        <value>${this.renderFileLink(job.job_id, 'increases', files.increases_file)}</value>
                    </div>
                    <div class="detail-item">
                        <label>Decreases File</label>
                        <value>${this.renderFileLink(job.job_id, 'decreases', files.decreases_file)}</value>
                    </div>
                </div>
            </div>

            ${charts.increases || charts.decreases ? `
                <div class="detail-section">
                    <h3>Charts Generated</h3>
                    <div class="detail-grid">
                        ${charts.increases ? `
                            <div class="detail-item">
                                <label>Increases Chart</label>
                                <value>${charts.increases}</value>
                            </div>
                        ` : ''}
                        ${charts.decreases ? `
                            <div class="detail-item">
                                <label>Decreases Chart</label>
                                <value>${charts.decreases}</value>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}

            ${job.error ? `
                <div class="detail-section">
                    <h3>Error Details</h3>
                    <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px;">
                        ${job.error}
                    </div>
                </div>
            ` : ''}
        `;

        modal.classList.add('active');
    }

    /**
     * Close job details modal
     */
    closeDetailsModal() {
        const modal = document.getElementById('jobDetailsModal');
        modal.classList.remove('active');
    }

    /**
     * Render a file download link or N/A if file doesn't exist
     */
    renderFileLink(jobId, fileType, filename) {
        if (!filename) {
            return 'N/A';
        }

        const downloadUrl = `/api/history/${jobId}/download/${fileType}`;
        return `<a href="${downloadUrl}" style="color: #007bff; text-decoration: none; font-weight: 600;" download>
            📥 ${filename}
        </a>`;
    }

    /**
     * Resend emails for a job
     */
    async resendEmails(jobId, weekNum) {
        // Store the job ID for later use
        this.currentResendJobId = jobId;

        // Show email preview modal using the EmailManager
        if (window.emailManager) {
            // Set a flag so EmailManager knows we're in resend mode
            window.emailManager.resendMode = true;
            window.emailManager.resendJobId = jobId;

            await window.emailManager.showEmailPreview(weekNum);
        } else {
            // Fallback to direct send if EmailManager is not available
            if (!confirm(`Are you sure you want to resend email notifications for Week ${weekNum}?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/history/${jobId}/resend-emails`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (data.success) {
                    alert(`Email notifications sent successfully!\n\nEmails sent: ${data.emails_sent || 0}`);
                } else {
                    alert(`Failed to send emails: ${data.error}`);
                }
            } catch (error) {
                console.error('Error resending emails:', error);
                alert(`Error: ${error.message}`);
            }
        }
    }

    /**
     * Delete a job
     */
    async deleteJob(jobId) {
        if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/history/${jobId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                alert('Job deleted successfully');
                this.loadHistory();
                this.loadStats();
            } else {
                alert(`Failed to delete job: ${data.error}`);
            }
        } catch (error) {
            console.error('Error deleting job:', error);
            alert(`Error: ${error.message}`);
        }
    }
}
