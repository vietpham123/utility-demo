// ============================================================
// Phase 2-3 Extensions: Login, Search, Hash routing, WebSocket,
// Pagination, Export, new service tabs, Settings
// ============================================================

(function() {
'use strict';

// --- State ---
let currentUser = null;
let wsConnection = null;
let liveEvents = [];

// --- Hash-based routing ---
function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    if (window.location.hash) handleRoute();
}

function handleRoute() {
    const hash = window.location.hash.replace('#', '').replace('/', '');
    if (!hash) return;
    const validSections = ['overview','scada','outages','metering','grid','reliability','forecast',
        'crew','notifications','weather','health','featureflags','customers','pricing',
        'workorders','auditlog','alertcorrelation','settings','livefeed'];
    if (validSections.includes(hash)) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        const el = document.getElementById(hash);
        if (el) {
            el.classList.add('active');
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.nav button').forEach(b => {
                if (b.getAttribute('data-section') === hash) b.classList.add('active');
            });
            if (typeof currentSection !== 'undefined') currentSection = hash;
            if (typeof fetchData === 'function') fetchData();
            fetchExtendedData(hash);
        }
    }
}

// --- Login ---
function initLogin() {
    const saved = sessionStorage.getItem('utility_user');
    if (saved) {
        try { currentUser = JSON.parse(saved); showApp(); } catch(e) {}
    }
}

window.doLogin = async function() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    const btn = document.getElementById('login-submit');
    if (!username || !password) { errEl.textContent = 'Please enter username and password'; errEl.style.display = 'block'; return; }
    btn.disabled = true; btn.textContent = 'Signing in...';
    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (resp.ok && data.token) {
            currentUser = { username: data.user?.username || username, name: data.user?.name || username, token: data.token, role: data.user?.role || 'operator' };
            sessionStorage.setItem('utility_user', JSON.stringify(currentUser));
            showApp();
        } else {
            errEl.textContent = data.error || 'Invalid credentials';
            errEl.style.display = 'block';
        }
    } catch(e) {
        // Fallback: allow demo login without customer-service
        currentUser = { username, name: username, token: 'demo-token', role: 'operator' };
        sessionStorage.setItem('utility_user', JSON.stringify(currentUser));
        showApp();
    }
    btn.disabled = false; btn.textContent = 'Sign In';
};

window.doLogout = function() {
    currentUser = null;
    sessionStorage.removeItem('utility_user');
    document.getElementById('login-overlay').classList.remove('hidden');
    document.querySelector('.main-app').style.display = 'none';
};

function showApp() {
    document.getElementById('login-overlay').classList.add('hidden');
    document.querySelector('.main-app').style.display = 'block';
    const nameEl = document.getElementById('user-display-name');
    const avatarEl = document.getElementById('user-avatar-letter');
    if (nameEl && currentUser) nameEl.textContent = currentUser.name;
    if (avatarEl && currentUser) avatarEl.textContent = (currentUser.name || 'U')[0].toUpperCase();
}

// --- Search ---
let searchTimeout = null;
window.handleSearch = function(e) {
    clearTimeout(searchTimeout);
    const q = e.target.value.trim();
    const results = document.getElementById('search-results');
    if (q.length < 2) { results.classList.remove('show'); return; }
    searchTimeout = setTimeout(async () => {
        try {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
            const data = await resp.json();
            renderSearchResults(data.results || {}, results);
        } catch(err) {
            results.innerHTML = '<div class="search-item">Search unavailable</div>';
            results.classList.add('show');
        }
    }, 300);
};

function renderSearchResults(results, container) {
    let html = '';
    const categories = [
        { key: 'outages', label: 'Outages', section: 'outages' },
        { key: 'customers', label: 'Customers', section: 'customers' },
        { key: 'workOrders', label: 'Work Orders', section: 'workorders' },
        { key: 'meters', label: 'Meters', section: 'metering' },
        { key: 'crews', label: 'Crews', section: 'crew' },
        { key: 'auditLogs', label: 'Audit Logs', section: 'auditlog' }
    ];
    let hasResults = false;
    for (const cat of categories) {
        const items = results[cat.key] || [];
        if (items.length === 0) continue;
        hasResults = true;
        html += `<div class="search-category">${cat.label} (${items.length})</div>`;
        items.slice(0, 5).forEach(item => {
            const display = item.id || item.name || item.location || item.username || JSON.stringify(item).substring(0, 60);
            html += `<div class="search-item" onclick="window.location.hash='${cat.section}';document.getElementById('search-results').classList.remove('show');document.getElementById('search-input').value=''">
                <span>${escHtml(String(display))}</span><span class="search-type">${cat.label}</span></div>`;
        });
    }
    if (!hasResults) html = '<div class="search-item">No results found</div>';
    container.innerHTML = html;
    container.classList.add('show');
}

// Close search on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-bar')) {
        const sr = document.getElementById('search-results');
        if (sr) sr.classList.remove('show');
    }
});

// --- WebSocket Live Feed ---
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    try {
        wsConnection = new WebSocket(wsUrl);
        wsConnection.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'connected') return;
                liveEvents.unshift({ ...data, receivedAt: new Date() });
                if (liveEvents.length > 100) liveEvents.pop();
                renderLiveFeed();
                showToast(data.message || `Event: ${data.type}`, data.severity === 'critical' ? 'error' : 'success');
            } catch(e) {}
        };
        wsConnection.onclose = () => { setTimeout(initWebSocket, 5000); };
        wsConnection.onerror = () => {};
    } catch(e) {}
}

function renderLiveFeed() {
    const container = document.getElementById('live-feed-list');
    if (!container) return;
    container.innerHTML = liveEvents.slice(0, 50).map(ev => {
        const typeClass = ev.type?.includes('outage') ? 'outage' : ev.type?.includes('scada') ? 'scada' :
            ev.type?.includes('crew') ? 'crew' : ev.type?.includes('weather') ? 'weather' :
            ev.type?.includes('work') ? 'work' : ev.type?.includes('meter') ? 'meter' : 'pricing';
        const time = ev.receivedAt ? ev.receivedAt.toLocaleTimeString() : '';
        return `<div class="live-event">
            <span class="ev-time">${time}</span>
            <span class="ev-type ev-type-${typeClass}">${(ev.type || '').replace(/_/g, ' ')}</span>
            <span class="ev-msg">${escHtml(ev.message || '')}</span>
            <span class="severity-${ev.severity || 'low'}">${ev.severity || ''}</span>
        </div>`;
    }).join('');
}

// --- Toast Notifications ---
function showToast(message, type) {
    let container = document.querySelector('.toast-container');
    if (!container) { container = document.createElement('div'); container.className = 'toast-container'; document.body.appendChild(container); }
    const toast = document.createElement('div');
    toast.className = `toast ${type || ''}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 4000);
}

// --- Pagination Helper ---
function renderPagination(containerId, currentPage, totalPages, onPageChange) {
    const html = `<div class="pagination">
        <span>Page ${currentPage} of ${totalPages}</span>
        <div class="pagination-controls">
            <button ${currentPage <= 1 ? 'disabled' : ''} onclick="${onPageChange}(${currentPage - 1})">← Prev</button>
            ${Array.from({length: Math.min(totalPages, 5)}, (_, i) => {
                const p = currentPage <= 3 ? i + 1 : currentPage + i - 2;
                if (p < 1 || p > totalPages) return '';
                return `<button class="${p === currentPage ? 'active' : ''}" onclick="${onPageChange}(${p})">${p}</button>`;
            }).join('')}
            <button ${currentPage >= totalPages ? 'disabled' : ''} onclick="${onPageChange}(${currentPage + 1})">Next →</button>
        </div>
    </div>`;
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = html;
}

// --- CSV Export ---
window.exportCSV = function(data, filename) {
    if (!data || data.length === 0) { showToast('No data to export', 'error'); return; }
    const headers = Object.keys(data[0]);
    const csv = [headers.join(','), ...data.map(row => headers.map(h => {
        let val = String(row[h] || '');
        if (val.includes(',') || val.includes('"') || val.includes('\n')) val = `"${val.replace(/"/g, '""')}"`;
        return val;
    }).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename || 'export.csv';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    showToast(`Exported ${data.length} rows to ${filename}`, 'success');
};

// --- Error State ---
function renderError(containerId, message, retryFn) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = `<div class="error-state">
        <div class="error-icon">⚠️</div>
        <div class="error-text">${escHtml(message)}</div>
        <button class="retry-btn" onclick="${retryFn}">Retry</button>
    </div>`;
}

// --- Fetch helpers ---
async function fetchJ(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// --- Extended Section Data Fetchers ---
function fetchExtendedData(section) {
    switch(section) {
        case 'customers': fetchCustomers(); break;
        case 'pricing': fetchPricing(); break;
        case 'workorders': fetchWorkOrders(); break;
        case 'auditlog': fetchAuditLog(); break;
        case 'alertcorrelation': fetchAlertCorrelation(); break;
        case 'livefeed': renderLiveFeed(); break;
    }
}

// --- Customers ---
let customerPage = 1;
async function fetchCustomers(page) {
    customerPage = page || 1;
    const container = document.getElementById('customer-table');
    const statsContainer = document.getElementById('customer-kpis');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading customers...</div>';
    try {
        const [customers, stats] = await Promise.all([
            fetchJ(`/api/customers?page=${customerPage}&limit=20`),
            fetchJ('/api/customers/stats')
        ]);
        if (statsContainer && stats) {
            statsContainer.innerHTML = [
                kpi('Total Customers', stats.total || stats.totalCustomers || '-', 'accounts', 'info'),
                kpi('Active', stats.active || '-', 'currently active', 'good'),
                kpi('Regions', stats.regions || stats.regionCount || '6', 'coverage areas', 'info'),
                kpi('Avg Usage', stats.avgUsage ? stats.avgUsage + ' kWh' : '-', 'monthly', 'info')
            ].join('');
        }
        const cList = customers.customers || customers || [];
        window._customerData = cList;
        container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div class="filter-bar">
                <span class="filter-label">Region:</span>
                <select onchange="filterCustomers(this.value)"><option value="">All</option>
                    <option>northeast</option><option>southeast</option><option>midwest</option>
                    <option>southwest</option><option>northwest</option><option>central</option></select>
            </div>
            <button class="export-btn" onclick="exportCSV(window._customerData,'customers.csv')">📥 Export CSV</button>
        </div>
        <table><tr><th>ID</th><th>Name</th><th>Account</th><th>Region</th><th>Type</th><th>Status</th></tr>
        ${cList.map(c => `<tr><td>${c.id || ''}</td><td>${escHtml(c.name || '')}</td><td>${c.accountNumber || ''}</td>
            <td>${c.region || ''}</td><td>${c.type || c.customerType || ''}</td><td>${c.status || 'active'}</td></tr>`).join('')}
        </table>`;
        if (customers.totalPages > 1) {
            container.innerHTML += `<div id="customer-pagination"></div>`;
            renderPagination('customer-pagination', customerPage, customers.totalPages, 'fetchCustomersPage');
        }
    } catch(e) {
        renderError('customer-table', 'Failed to load customers: ' + e.message, 'fetchCustomers()');
    }
}
window.fetchCustomers = fetchCustomers;
window.fetchCustomersPage = function(p) { fetchCustomers(p); };
window.filterCustomers = async function(region) {
    if (!region) { fetchCustomers(1); return; }
    const container = document.getElementById('customer-table');
    try {
        const data = await fetchJ(`/api/customers/region/${region}`);
        const cList = data.customers || data || [];
        window._customerData = cList;
        container.innerHTML = `<table><tr><th>ID</th><th>Name</th><th>Account</th><th>Region</th><th>Type</th><th>Status</th></tr>
        ${cList.map(c => `<tr><td>${c.id||''}</td><td>${escHtml(c.name||'')}</td><td>${c.accountNumber||''}</td>
            <td>${c.region||''}</td><td>${c.type||c.customerType||''}</td><td>${c.status||'active'}</td></tr>`).join('')}
        </table>`;
    } catch(e) { renderError('customer-table', e.message, 'fetchCustomers()'); }
};

// --- Pricing ---
async function fetchPricing() {
    const container = document.getElementById('pricing-detail');
    const kpiContainer = document.getElementById('pricing-kpis');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading pricing...</div>';
    try {
        const [current, rates, regions] = await Promise.all([
            fetchJ('/api/pricing/current'),
            fetchJ('/api/pricing/rates'),
            fetchJ('/api/pricing/regions')
        ]);
        if (kpiContainer && current) {
            kpiContainer.innerHTML = [
                kpi('Current Rate', current.currentRate ? '$' + current.currentRate + '/kWh' : '-', current.period || 'base rate', 'info'),
                kpi('Rate Period', current.period || '-', current.timeOfUse || '', 'info'),
                kpi('Fuel Adjustment', current.fuelAdjustment ? '$' + current.fuelAdjustment : '-', 'per kWh', 'warning'),
                kpi('Rate Classes', rates?.length || current.rateClasses || '5', 'available', 'info')
            ].join('');
        }
        const rateList = rates?.rates || rates || [];
        const regionList = regions?.regions || regions || [];
        container.innerHTML = `<div class="grid-2">
            <div class="panel"><div class="panel-header"><h3>Rate Classes</h3></div><div class="panel-body">
                <table><tr><th>Class</th><th>Name</th><th>Base</th><th>Peak</th><th>Off-Peak</th></tr>
                ${rateList.map(r => `<tr><td>${r.id || r.code || ''}</td><td>${r.name || ''}</td>
                    <td>$${(r.baseRate || r.base || 0).toFixed(4)}</td><td>$${(r.peakRate || r.peak || 0).toFixed(4)}</td>
                    <td>$${(r.offPeakRate || r.offPeak || 0).toFixed(4)}</td></tr>`).join('')}
                </table></div></div>
            <div class="panel"><div class="panel-header"><h3>Rate Calculator</h3></div><div class="panel-body">
                <div class="form-row">
                    <div class="form-group"><label>Rate Class</label><select id="calc-rate-class">
                        ${rateList.map(r => `<option value="${r.id || r.code}">${r.name || r.id || r.code}</option>`).join('')}
                    </select></div>
                    <div class="form-group"><label>Region</label><select id="calc-region">
                        ${regionList.map(r => `<option value="${r.id || r.name}">${r.name || r.id}</option>`).join('')}
                    </select></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>kWh Usage</label><input type="number" id="calc-kwh" value="1000" min="0"></div>
                    <div class="form-group" style="flex:0"><label>&nbsp;</label><button class="btn btn-primary" onclick="calculateRate()">Calculate</button></div>
                </div>
                <div id="calc-result" style="margin-top:12px;padding:12px;background:#0d1117;border-radius:6px;display:none"></div>
            </div></div>
        </div>`;
    } catch(e) {
        renderError('pricing-detail', 'Failed to load pricing: ' + e.message, 'fetchPricing()');
    }
}
window.fetchPricing = fetchPricing;
window.calculateRate = async function() {
    const rateClass = document.getElementById('calc-rate-class')?.value;
    const region = document.getElementById('calc-region')?.value;
    const kwh = document.getElementById('calc-kwh')?.value || 1000;
    const result = document.getElementById('calc-result');
    if (!result) return;
    try {
        const data = await fetchJ(`/api/pricing/calculate?rateClass=${rateClass}&region=${region}&kwh=${kwh}`);
        result.style.display = 'block';
        result.innerHTML = `<div style="font-size:20px;font-weight:700;color:#3fb950;">$${(data.totalCost || data.total || 0).toFixed(2)}</div>
            <div style="font-size:11px;color:#8b949e;margin-top:4px;">Estimated monthly cost for ${kwh} kWh</div>
            ${data.breakdown ? `<div style="margin-top:8px;font-size:11px;color:#8b949e;">${Object.entries(data.breakdown).map(([k,v]) => `${k}: $${v.toFixed(2)}`).join(' · ')}</div>` : ''}`;
    } catch(e) { result.style.display = 'block'; result.innerHTML = `<span style="color:#f85149">Calculation failed: ${e.message}</span>`; }
};

// --- Work Orders ---
let woPage = 1;
async function fetchWorkOrders(page) {
    woPage = page || 1;
    const container = document.getElementById('workorder-table');
    const kpiContainer = document.getElementById('workorder-kpis');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading work orders...</div>';
    try {
        const [orders, stats] = await Promise.all([
            fetchJ(`/api/work-orders?page=${woPage}&limit=20`),
            fetchJ('/api/work-orders/stats')
        ]);
        if (kpiContainer && stats) {
            kpiContainer.innerHTML = [
                kpi('Total Orders', stats.total || '-', 'all time', 'info'),
                kpi('Open', stats.open || stats.pending || '-', 'in progress', 'warning'),
                kpi('Completed', stats.completed || '-', 'this month', 'good'),
                kpi('Emergency', stats.emergency || '-', 'high priority', stats.emergency > 0 ? 'critical' : 'good')
            ].join('');
        }
        const woList = orders.workOrders || orders.work_orders || orders || [];
        window._workOrderData = woList;
        container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <button class="btn btn-primary btn-sm" onclick="showCreateWorkOrder()">+ New Work Order</button>
            <button class="export-btn" onclick="exportCSV(window._workOrderData,'work-orders.csv')">📥 Export CSV</button>
        </div>
        <table><tr><th>ID</th><th>Type</th><th>Priority</th><th>Status</th><th>Location</th><th>Assigned</th><th>Created</th></tr>
        ${woList.map(w => `<tr class="wo-${(w.priority||'medium').toLowerCase()}"><td>${w.id||''}</td><td>${w.type||w.workType||''}</td>
            <td><span class="severity-${(w.priority||'medium').toLowerCase()}">${w.priority||''}</span></td>
            <td>${w.status||''}</td><td>${escHtml(w.location||'')}</td><td>${w.assignedTo||w.assigned||'-'}</td>
            <td>${w.createdAt ? new Date(w.createdAt).toLocaleDateString() : ''}</td></tr>`).join('')}
        </table>`;
        if (orders.totalPages > 1) {
            container.innerHTML += '<div id="wo-pagination"></div>';
            renderPagination('wo-pagination', woPage, orders.totalPages, 'fetchWOPage');
        }
    } catch(e) {
        renderError('workorder-table', 'Failed to load work orders: ' + e.message, 'fetchWorkOrders()');
    }
}
window.fetchWorkOrders = fetchWorkOrders;
window.fetchWOPage = function(p) { fetchWorkOrders(p); };

window.showCreateWorkOrder = function() {
    const body = `<div class="form-row"><div class="form-group"><label>Work Type</label>
        <select id="wo-type"><option>repair</option><option>inspection</option><option>maintenance</option>
            <option>emergency</option><option>vegetation</option><option>equipment_replacement</option></select></div>
        <div class="form-group"><label>Priority</label>
        <select id="wo-priority"><option>low</option><option>medium</option><option selected>high</option><option>emergency</option></select></div></div>
        <div class="form-row"><div class="form-group"><label>Location</label><input id="wo-location" placeholder="e.g. 123 Main St, Northeast"></div></div>
        <div class="form-row"><div class="form-group"><label>Description</label><textarea id="wo-desc" placeholder="Describe the work required..."></textarea></div></div>
        <div class="form-row"><div class="form-group"><label>Assigned To</label><input id="wo-assigned" placeholder="Crew or technician name"></div></div>`;
    const actions = `<button class="modal-btn primary" onclick="submitWorkOrder()">Create Work Order</button>
        <button class="modal-btn" onclick="closeModal()">Cancel</button>`;
    if (typeof showModal === 'function') showModal('📋 Create Work Order', body, actions);
};

window.submitWorkOrder = async function() {
    const wo = {
        type: document.getElementById('wo-type')?.value,
        priority: document.getElementById('wo-priority')?.value,
        location: document.getElementById('wo-location')?.value,
        description: document.getElementById('wo-desc')?.value,
        assignedTo: document.getElementById('wo-assigned')?.value
    };
    try {
        await fetch('/api/work-orders', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(wo) });
        if (typeof closeModal === 'function') closeModal();
        showToast('Work order created successfully', 'success');
        fetchWorkOrders();
    } catch(e) { showToast('Failed to create work order: ' + e.message, 'error'); }
};

// --- Audit Log ---
let auditPage = 1;
async function fetchAuditLog(page) {
    auditPage = page || 1;
    const container = document.getElementById('audit-table');
    const kpiContainer = document.getElementById('audit-kpis');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading audit log...</div>';
    try {
        const [logs, stats] = await Promise.all([
            fetchJ(`/api/audit/log?page=${auditPage}&limit=30`),
            fetchJ('/api/audit/stats')
        ]);
        if (kpiContainer && stats) {
            kpiContainer.innerHTML = [
                kpi('Total Entries', stats.total || stats.totalEntries || '-', 'recorded events', 'info'),
                kpi('Critical', stats.critical || '-', 'events', stats.critical > 0 ? 'critical' : 'good'),
                kpi('Warning', stats.warning || '-', 'events', 'warning'),
                kpi('Today', stats.today || '-', 'entries', 'info')
            ].join('');
        }
        const entries = logs.entries || logs.log || logs || [];
        window._auditData = entries;
        container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div class="filter-bar">
                <span class="filter-label">Severity:</span>
                <select onchange="filterAudit(this.value)"><option value="">All</option>
                    <option>critical</option><option>high</option><option>medium</option><option>low</option><option>info</option></select>
            </div>
            <button class="export-btn" onclick="exportCSV(window._auditData,'audit-log.csv')">📥 Export CSV</button>
        </div>
        <table><tr><th>Time</th><th>Event Type</th><th>Severity</th><th>Source</th><th>Details</th></tr>
        ${entries.map(e => `<tr><td style="white-space:nowrap">${e.timestamp ? new Date(e.timestamp).toLocaleString() : ''}</td>
            <td>${e.eventType||e.event_type||''}</td>
            <td><span class="severity-${(e.severity||'info').toLowerCase()}">${e.severity||''}</span></td>
            <td>${e.source||''}</td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis">${escHtml(e.details||e.message||'')}</td></tr>`).join('')}
        </table>`;
        if (logs.totalPages > 1) {
            container.innerHTML += '<div id="audit-pagination"></div>';
            renderPagination('audit-pagination', auditPage, logs.totalPages, 'fetchAuditPage');
        }
    } catch(e) {
        renderError('audit-table', 'Failed to load audit log: ' + e.message, 'fetchAuditLog()');
    }
}
window.fetchAuditLog = fetchAuditLog;
window.fetchAuditPage = function(p) { fetchAuditLog(p); };
window.filterAudit = async function(severity) {
    if (!severity) { fetchAuditLog(1); return; }
    const container = document.getElementById('audit-table');
    try {
        const data = await fetchJ(`/api/audit/log?severity=${severity}`);
        const entries = data.entries || data || [];
        container.innerHTML = `<table><tr><th>Time</th><th>Event Type</th><th>Severity</th><th>Source</th><th>Details</th></tr>
        ${entries.map(e => `<tr><td>${e.timestamp ? new Date(e.timestamp).toLocaleString() : ''}</td>
            <td>${e.eventType||''}</td><td><span class="severity-${(e.severity||'info').toLowerCase()}">${e.severity||''}</span></td>
            <td>${e.source||''}</td><td style="max-width:250px;overflow:hidden;text-overflow:ellipsis">${escHtml(e.details||e.message||'')}</td></tr>`).join('')}
        </table>`;
    } catch(e) { renderError('audit-table', e.message, 'fetchAuditLog()'); }
};

// --- Alert Correlation ---
async function fetchAlertCorrelation() {
    const container = document.getElementById('alert-corr-table');
    const kpiContainer = document.getElementById('alert-corr-kpis');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading correlated alerts...</div>';
    try {
        const [alerts, stats] = await Promise.all([
            fetchJ('/api/alerts/correlated?limit=30'),
            fetchJ('/api/alerts/stats')
        ]);
        if (kpiContainer && stats) {
            kpiContainer.innerHTML = [
                kpi('Correlated', stats.total || stats.correlated || '-', 'alert clusters', 'info'),
                kpi('Critical', stats.critical || '-', 'high severity', stats.critical > 0 ? 'critical' : 'good'),
                kpi('SCADA-Weather', stats.scadaWeather || '-', 'correlations', 'warning'),
                kpi('Accuracy', stats.accuracy ? stats.accuracy + '%' : '-', 'correlation confidence', 'good')
            ].join('');
        }
        const alertList = alerts.alerts || alerts.correlated || alerts || [];
        window._alertData = alertList;
        container.innerHTML = `<div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
            <button class="export-btn" onclick="exportCSV(window._alertData,'correlated-alerts.csv')">📥 Export CSV</button>
        </div>
        <table><tr><th>Time</th><th>Type</th><th>Severity</th><th>Region</th><th>SCADA</th><th>Weather</th><th>Confidence</th></tr>
        ${alertList.map(a => `<tr><td style="white-space:nowrap">${a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}</td>
            <td>${a.type||a.alertType||''}</td>
            <td><span class="severity-${(a.severity||'medium').toLowerCase()}">${a.severity||''}</span></td>
            <td>${a.region||''}</td><td>${a.scadaAlert||a.scada||'-'}</td><td>${a.weatherCondition||a.weather||'-'}</td>
            <td>${a.confidence ? (a.confidence * 100).toFixed(0) + '%' : a.correlationScore || '-'}</td></tr>`).join('')}
        </table>`;
    } catch(e) {
        renderError('alert-corr-table', 'Failed to load alerts: ' + e.message, 'fetchAlertCorrelation()');
    }
}
window.fetchAlertCorrelation = fetchAlertCorrelation;

// --- Settings ---
window.saveSetting = function(key, value) {
    localStorage.setItem('utility_' + key, value);
    showToast('Setting saved', 'success');
    if (key === 'refreshInterval') {
        // Could reinitialize polling interval here
    }
};

function loadSettings() {
    const theme = localStorage.getItem('utility_theme') || 'dark';
    const refresh = localStorage.getItem('utility_refreshInterval') || '30';
    const tz = localStorage.getItem('utility_timezone') || 'local';
    const selects = {
        'setting-theme': theme,
        'setting-refresh': refresh,
        'setting-timezone': tz
    };
    Object.entries(selects).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.value = val;
    });
}

// --- Hook into existing fetchData ---
const origFetchData = window.fetchData;
window.fetchData = function() {
    if (origFetchData) origFetchData();
    const section = typeof currentSection !== 'undefined' ? currentSection : '';
    fetchExtendedData(section);
};

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    initLogin();
    initRouter();
    initWebSocket();
    loadSettings();

    // Enter key on login form
    const loginPass = document.getElementById('login-password');
    if (loginPass) loginPass.addEventListener('keypress', (e) => { if (e.key === 'Enter') doLogin(); });

    // Enter key on search
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') e.preventDefault(); });
});

})();
