// Results Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeResultsPage();
});

function initializeResultsPage() {
    // Add any interactive features for the results page
    addChartInteractivity();
    addDownloadTracking();
}

function addChartInteractivity() {
    const chartImages = document.querySelectorAll('.chart-image');

    chartImages.forEach(img => {
        img.addEventListener('click', function() {
            // Open chart in modal or new tab
            window.open(this.src, '_blank');
        });

        // Add hover effect
        img.style.cursor = 'pointer';
        img.title = 'Click to view larger';
    });
}

function addDownloadTracking() {
    const downloadLinks = document.querySelectorAll('a[download]');

    downloadLinks.forEach(link => {
        link.addEventListener('click', function() {
            const filename = this.getAttribute('download');
            console.log(`Download started: ${filename}`);

            // You could send analytics here
            // trackDownload(filename);
        });
    });
}

function trackDownload(filename) {
    // Optional: Send download analytics
    fetch('/analytics/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: filename,
            timestamp: new Date().toISOString()
        })
    }).catch(err => {
        console.log('Analytics tracking failed:', err);
    });
}