// Global state
let currentFilename = null;
let currentChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const dropZone = document.querySelector('.drop-zone');
    if (dropZone) {
        setupDropZone(dropZone);
    }
    
    // Initialize dashboard if on dashboard page
    if (document.querySelector('.dashboard-layout')) {
        initializeDashboard();
    }
});

// Setup drag and drop
function setupDropZone(dropZone) {
    const fileInput = document.querySelector('input[type="file"]');
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

// Initialize dashboard
function initializeDashboard() {
    currentFilename = document.querySelector('meta[name="filename"]')?.content || '';
    
    // Load preview
    loadPreview();
    
    // Setup sidebar navigation
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Setup visualization controls
    const vizBtn = document.getElementById('createVizBtn');
    if (vizBtn) {
        vizBtn.addEventListener('click', createVisualization);
    }
    
    // Setup export buttons
    document.querySelectorAll('.export-btn').forEach(btn => {
        btn.addEventListener('click', exportData);
    });
    
    // Auto-create initial visualization
    setTimeout(() => {
        createVisualization();
    }, 500);
}

// Load data preview
function loadPreview() {
    if (!currentFilename) return;
    
    fetch(`/api/preview/${currentFilename}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                return;
            }
            renderTable(data);
        })
        .catch(error => {
            showAlert('error', 'Failed to load data preview');
            console.error(error);
        });
}

// Render table
function renderTable(data) {
    const container = document.getElementById('previewContainer');
    if (!container) return;
    
    let html = '<table class="table"><thead><tr>';
    data.columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    data.data.slice(0, 20).forEach(row => {
        html += '<tr>';
        data.columns.forEach(col => {
            let value = row[col];
            if (value === null || value === undefined) value = '';
            if (typeof value === 'number') value = value.toFixed(2);
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += `<p class="text-muted">Showing ${Math.min(data.data.length, 20)} of ${data.total_rows} rows</p>`;
    
    container.innerHTML = html;
}

// Switch tabs
function switchTab(tabId) {
    // Update sidebar items
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabId);
    });
    
    // Update tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabId);
    });
    
    // Load data for specific tabs
    if (tabId === 'statistics') {
        loadStatistics();
    } else if (tabId === 'quality') {
        loadQualityReport();
    }
}

// Load statistics
function loadStatistics() {
    // Implementation for loading statistics
}

// Load quality report
function loadQualityReport() {
    if (!currentFilename) return;
    
    fetch(`/api/quality_report/${currentFilename}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                return;
            }
            renderQualityReport(data);
        })
        .catch(error => {
            console.error(error);
        });
}

// Render quality report
function renderQualityReport(data) {
    const container = document.getElementById('qualityReport');
    if (!container) return;
    
    let html = '<div class="grid-2">';
    
    // Missing data
    html += '<div class="card"><div class="card-header"><h3>Missing Data</h3></div>';
    const missingData = data.missing_data || {};
    if (Object.keys(missingData).length === 0) {
        html += '<p class="text-muted">No missing data found</p>';
    } else {
        html += '<table class="table"><thead><tr><th>Column</th><th>Missing Count</th><th>Percentage</th></tr></thead><tbody>';
        for (const [col, info] of Object.entries(missingData)) {
            html += `<tr><td>${col}</td><td>${info.count}</td><td>${info.percentage.toFixed(1)}%</td></tr>`;
        }
        html += '</tbody></table>';
    }
    html += '</div>';
    
    // Outliers
    html += '<div class="card"><div class="card-header"><h3>Outliers</h3></div>';
    const outliers = data.outliers || {};
    if (Object.keys(outliers).length === 0) {
        html += '<p class="text-muted">No outliers detected</p>';
    } else {
        html += '<table class="table"><thead><tr><th>Column</th><th>Outliers</th><th>Percentage</th></tr></thead><tbody>';
        for (const [col, info] of Object.entries(outliers)) {
            html += `<tr><td>${col}</td><td>${info.count}</td><td>${info.percentage.toFixed(1)}%</td></tr>`;
        }
        html += '</tbody></table>';
    }
    html += '</div>';
    
    html += '</div>';
    
    container.innerHTML = html;
}

// Create visualization
function createVisualization() {
    const vizType = document.getElementById('vizType')?.value;
    const column = document.getElementById('vizColumn')?.value;
    const xCol = document.getElementById('xColumn')?.value;
    const yCol = document.getElementById('yColumn')?.value;
    const colorCol = document.getElementById('colorColumn')?.value;
    const bins = parseInt(document.getElementById('bins')?.value) || 30;
    const topN = parseInt(document.getElementById('topN')?.value) || 20;
    
    if (!currentFilename) {
        showAlert('error', 'No file loaded');
        return;
    }
    
    // Build request data
    const data = { type: vizType };
    switch (vizType) {
        case 'histogram':
            if (!column) { showAlert('error', 'Please select a column'); return; }
            data.column = column;
            data.bins = bins;
            break;
        case 'boxplot':
            if (!column) { showAlert('error', 'Please select a column'); return; }
            data.column = column;
            break;
        case 'scatter':
            if (!xCol || !yCol) { showAlert('error', 'Please select X and Y columns'); return; }
            data.x_col = xCol;
            data.y_col = yCol;
            data.color_col = colorCol || null;
            break;
        case 'barchart':
            if (!column) { showAlert('error', 'Please select a column'); return; }
            data.column = column;
            data.top_n = topN;
            break;
        case 'piechart':
            if (!column) { showAlert('error', 'Please select a column'); return; }
            data.column = column;
            data.top_n = topN;
            break;
        case 'line':
            if (!xCol || !yCol) { showAlert('error', 'Please select X and Y columns'); return; }
            data.x_col = xCol;
            data.y_col = yCol;
            break;
        case 'correlation':
            // No additional data needed
            break;
        default:
            showAlert('error', 'Invalid visualization type');
            return;
    }
    
    // Show loading
    const container = document.getElementById('visualizationContainer');
    container.innerHTML = '<div style="display:flex;justify-content:center;padding:60px;"><div class="spinner"></div></div>';
    
    // Fetch visualization
    fetch(`/api/visualize/${currentFilename}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            showAlert('error', result.error);
            container.innerHTML = '<p class="text-muted" style="text-align:center;padding:40px;">' + result.error + '</p>';
            return;
        }
        
        if (result.figure) {
            renderPlotly(container, result.figure);
        }
    })
    .catch(error => {
        showAlert('error', 'Failed to create visualization');
        console.error(error);
    });
}

// Render Plotly chart
function renderPlotly(container, figureJson) {
    try {
        const figure = JSON.parse(figureJson);
        Plotly.react(container, figure.data, figure.layout, {responsive: true});
    } catch (error) {
        console.error('Error rendering Plotly chart:', error);
        container.innerHTML = '<p class="text-muted" style="text-align:center;padding:40px;">Error rendering chart</p>';
    }
}

// Export data
function exportData(e) {
    const format = e.target.dataset.format || 'csv';
    if (!currentFilename) {
        showAlert('error', 'No file loaded');
        return;
    }
    
    window.location.href = `/api/export/${currentFilename}/${format}`;
}

// Show alert
function showAlert(type, message) {
    const container = document.getElementById('alertContainer');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()" style="background:none;border:none;font-size:20px;cursor:pointer;margin-left:auto;">×</button>`;
    
    container.appendChild(alert);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// Utility function to format numbers
function formatNumber(num) {
    if (num === null || num === undefined) return '';
    if (typeof num === 'number') {
        if (Number.isInteger(num)) {
            return num.toLocaleString();
        }
        return num.toFixed(2);
    }
    return num;
}