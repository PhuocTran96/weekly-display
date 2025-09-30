/**
 * Results Module - Handles results display and visualization
 */

export class ResultsManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const exportAlertsBtn = document.getElementById('exportAlertsBtn');
        if (exportAlertsBtn) {
            exportAlertsBtn.addEventListener('click', () => this.exportAlerts());
        }

        const alertFilter = document.getElementById('alertFilter');
        const searchInput = document.getElementById('searchInput');

        if (alertFilter) {
            alertFilter.addEventListener('change', () => this.filterAlerts());
        }

        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.filterAlerts(), 300));
        }
    }

    showResults(result) {
        this.updateStatistics(result.summary);
        this.updateCharts(result.charts);
        this.updateDownloadLinks(result);

        this.showSection('dashboardSection');
        this.showSection('downloadSection');

        // Show Send Email button after processing is complete
        this.showEmailButton();

        if (result.all_changes && result.all_changes.length > 0) {
            this.displayAlerts(result.all_changes);
            this.showSection('alertsSection');
        }
    }

    showEmailButton() {
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        if (sendEmailBtn) {
            sendEmailBtn.classList.remove('hidden');
        }
    }

    updateStatistics(summary) {
        const totalModels = summary.models_increased + summary.models_decreased + (summary.models_unchanged || 0);

        const stats = {
            'totalModels': totalModels,
            'modelsIncreased': summary.models_increased,
            'modelsDecreased': summary.models_decreased,
            'modelsUnchanged': summary.models_unchanged || 0
        };

        Object.entries(stats).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });
    }

    updateCharts(charts) {
        console.log('Updating charts:', charts);

        if (charts.increases) {
            this.setChartImage('increasesChart', 'increasesPlaceholder', `/charts/increases/${charts.increases}`);
        }

        if (charts.decreases) {
            this.setChartImage('decreasesChart', 'decreasesPlaceholder', `/charts/decreases/${charts.decreases}`);
        }
    }

    setChartImage(imgId, placeholderId, src) {
        const img = document.getElementById(imgId);
        const placeholder = document.getElementById(placeholderId);

        if (img) {
            img.src = src;
            img.classList.remove('hidden');
            if (placeholder) placeholder.style.display = 'none';
            console.log(`Set ${imgId} src:`, src);
        }
    }

    updateDownloadLinks(result) {
        const links = {
            'downloadReportLink': result.report_file,
            'downloadAlertsLink': result.alert_file,
            'downloadIncreasesLink': result.increases_file,
            'downloadDecreasesLink': result.decreases_file
        };

        Object.entries(links).forEach(([id, filename]) => {
            const link = document.getElementById(id);
            if (link && filename) {
                link.href = `/download/${filename}`;
                link.download = filename;
                link.classList.remove('disabled');
            }
        });

        this.updateChartDownloads(result.charts);
    }

    updateChartDownloads(charts) {
        const chartDownloads = document.getElementById('chartDownloads');
        if (!chartDownloads || !charts) return;

        chartDownloads.innerHTML = '';

        Object.entries(charts).forEach(([type, path]) => {
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

    displayAlerts(alerts) {
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

    filterAlerts() {
        const filterValue = document.getElementById('alertFilter')?.value || 'all';
        const searchValue = document.getElementById('searchInput')?.value.toLowerCase() || '';
        const tableBody = document.getElementById('alertsTableBody');

        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('tr');

        rows.forEach(row => {
            const model = row.cells[0].textContent.toLowerCase();
            const change = parseInt(row.cells[3].textContent);

            let showRow = true;

            if (filterValue === 'increases' && change <= 0) showRow = false;
            if (filterValue === 'decreases' && change >= 0) showRow = false;
            if (searchValue && !model.includes(searchValue)) showRow = false;

            row.style.display = showRow ? '' : 'none';
        });
    }

    exportAlerts() {
        const tableBody = document.getElementById('alertsTableBody');
        if (!tableBody) return;

        const rows = Array.from(tableBody.querySelectorAll('tr:not([style*="display: none"])'));
        const data = rows.map(row => ({
            Model: row.cells[0].textContent,
            Previous: parseInt(row.cells[1].textContent),
            Current: parseInt(row.cells[2].textContent),
            Change: parseInt(row.cells[3].textContent),
            Status: row.cells[4].textContent
        }));

        const csv = this.convertToCSV(data);
        this.downloadCSV(csv, 'filtered_alerts.csv');
    }

    convertToCSV(data) {
        if (!data.length) return '';

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
        ].join('\n');

        return csvContent;
    }

    downloadCSV(csv, filename) {
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

    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
            section.classList.add('fade-in');
        }
    }

    debounce(func, wait) {
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
}