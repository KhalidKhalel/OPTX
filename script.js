// OPTX Frontend - SPA logic, WebSocket communication, and UI management
let websocket = null;            // Global WebSocket instance for real-time traffic
let isBackendConnected = false;  // Heartbeat flag for the Python OSINT server
let sessionActive = false;       // Logic gate to prevent overlapping automation
let currentPhone = null;         // Cache for the active normalized phone number

/*============================================================================
   SPA NAVIGATION & ROUTING
   Handles view switching for Search, Removal, and About pages without
   reloading the browser. Manages URL history and active link styling.
============================================================================*/

/**
 * Standard Single Page Application (SPA) view switcher.
 * Hides all view-sections and exposes the target view by ID.
 */
function switchView(viewId) {
  // Hide all containers marked as view-sections
  document.querySelectorAll('.view-section').forEach(section => section.classList.add('hidden'));

  // Expose the requested view (e.g., 'searchView', 'removalView')
  const targetView = document.getElementById(viewId + 'View');
  if (targetView) targetView.classList.remove('hidden');

  // Sync navigation link highlight states
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    const linkText = link.textContent.toLowerCase().trim();
    if (linkText === viewId.toLowerCase() || (linkText === 'search' && viewId === 'search')) {
      link.classList.add('active');
    }
  });

  // Dynamic document title and URL hash management
  const titles = { 'search': 'OPTX - Search', 'removal': 'OPTX - Data Removal', 'about': 'OPTX - About' };
  document.title = titles[viewId] || 'OPTX - OSINT Assistant';
  window.history.pushState(null, '', '#' + (viewId === 'search' ? 'search' : viewId));

  // Toggle visibility of elements that should only appear on the Search page
  document.querySelectorAll('.home-only').forEach(el => {
    viewId === 'search' ? el.classList.remove('hidden') : el.classList.add('hidden');
  });

  // Toggle visibility of global elements that must be hidden on the About page
  document.querySelectorAll('.hide-on-about').forEach(el => {
    viewId === 'about' ? el.classList.add('hidden') : el.classList.remove('hidden');
  });

  // Handle restoration of search results when returning to the Search view
  if (viewId === 'search') {
    const results = document.getElementById('results');
    if (results && results.innerHTML.trim() !== '') results.classList.remove('hidden');
  } else {
    // Hide results when navigating away to keep UI focused
    const results = document.getElementById('results');
    if (results) results.classList.add('hidden');
  }
}

/**
 * Utility: Sanitizes raw text into safe HTML to prevent XSS.
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/*============================================================================
   BROWSER AUTOMATION UI
   Manages the live agent preview, real-time screenshots, and the fullscreen
   workspace for monitoring background automation.
============================================================================*/

/**
 * Prepares and shows the browser automation workspace.
 */
function showBrowserView(shouldSwitch = false) {
  if (shouldSwitch) switchView('removal');
  resetEndButton();
  const iframe = document.getElementById('browserUseIframe');
  const placeholder = document.getElementById('browserPlaceholder');
  const screenshot = document.getElementById('browserScreenshot');
  if (iframe) {
    iframe.classList.remove('hidden');
    placeholder.classList.add('hidden');
    screenshot.classList.add('hidden');
    document.getElementById('browserUrl').textContent = 'browser-use AI Agent (with element highlighting)';
  }
}

/**
 * Collapses the automation UI back to its ready state.
 */
function closeBrowserView() {
  document.getElementById('browserView').classList.add('hidden', 'fullscreen');
  const iframe = document.getElementById('browserUseIframe');
  const placeholder = document.getElementById('browserPlaceholder');
  if (iframe) iframe.classList.add('hidden');
  if (placeholder) placeholder.classList.remove('hidden');
}

function updateBrowserUrl(url) {
  document.getElementById('browserUrl').textContent = url;
}

/**
 * Renders a new base64 screenshot received from the backend agent.
 */
function updateBrowserScreenshot(base64Data) {
  const screenshot = document.getElementById('browserScreenshot');
  const placeholder = document.getElementById('browserPlaceholder');
  const iframe = document.getElementById('browserUseIframe');
  if (base64Data) {
    screenshot.src = 'data:image/png;base64,' + base64Data;
    screenshot.classList.remove('hidden');
    placeholder.classList.add('hidden');
    if (iframe) iframe.classList.add('hidden');
    resetEndButton();
  }
}

/**
 * Expands the browser preview to fill the entire viewport.
 */
function toggleBrowserFullscreen() {
  const browserView = document.getElementById('browserView');
  browserView.classList.toggle('fullscreen');
  const btn = document.querySelector('.browser-expand-btn i');
  btn.className = browserView.classList.contains('fullscreen') ? 'fas fa-compress' : 'fas fa-expand';
}

/*============================================================================
   SESSION LIFECYCLE MANAGEMENT
   Commands to start, monitor, and gracefully end automation tasks.
============================================================================*/

/**
 * Force-terminates an active session/automation via backend command.
 */
function endSession() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({ type: 'end_session' }));
  }
  const browserView = document.getElementById('browserView');
  if (browserView) browserView.classList.remove('fullscreen');
  const screenshot = document.getElementById('browserScreenshot');
  const placeholder = document.getElementById('browserPlaceholder');
  const liveFrame = document.getElementById('liveBrowserFrame');
  if (screenshot) { screenshot.src = ''; screenshot.classList.add('hidden'); }
  if (liveFrame) { liveFrame.src = ''; liveFrame.classList.add('hidden'); }
  if (placeholder) placeholder.classList.remove('hidden');
  const statusText = document.getElementById('browserStatusText');
  if (statusText) statusText.textContent = 'Status: Ready';
  const urlBar = document.getElementById('browserUrl');
  if (urlBar) urlBar.textContent = 'Ready for automation';
  sessionActive = false;
  addLogEntry('Session Closed.', 'system');
}

/**
 * Resets the End/X button for a fresh automation cycle.
 */
function resetEndButton() {
  const endBtn = document.getElementById('endSessionBtn');
  if (endBtn) {
    endBtn.innerHTML = '<i class="fas fa-times"></i> End';
    endBtn.disabled = false;
    endBtn.classList.remove('ended', 'hidden');
  }
}

/*============================================================================
   REMOVAL AUTOMATION ENGINE
   Gathers identity details and transmits them to the agent for processing.
============================================================================*/

/**
 * The core trigger for data broker removal.
 * Combines UI current values into a payload and alerts the backend.
 */
function initiateRemoval() {
  const requiredFields = ['userFirstName', 'userLastName', 'userStreet', 'userCity', 'userState', 'userZip', 'userPhone'];
  const missing = requiredFields.filter(id => !document.getElementById(id)?.value?.trim());

  if (missing.length > 0) {
    alert(`Please fill in all required fields:\n- ${missing.map(id => document.querySelector(`label[for="${id}"]`).innerText).join('\n- ')}`);
    return;
  }

  const userInfo = {
    first_name: document.getElementById('userFirstName')?.value || '',
    last_name: document.getElementById('userLastName')?.value || '',
    // Email is handled by backend now
    phone: document.getElementById('userPhone')?.value || '',
    street: document.getElementById('userStreet')?.value || '',
    city: document.getElementById('userCity')?.value || '',
    state: document.getElementById('userState')?.value || '',
    zip: document.getElementById('userZip')?.value || '',
    dob: document.getElementById('userDOB')?.value || '',
    age: document.getElementById('userAge')?.value || ''
  };

  // Persist one last time just in case
  saveFormData();

  localStorage.setItem('optx_user_info', JSON.stringify(userInfo));
  showBrowserView(true);
  updateBrowserUrl('Preparing removal process...');
  addLogEntry('Initiating removal process...', 'system');
  if (!isBackendConnected) {
    addLogEntry('Error: Not connected to backend.', 'error');
  } else {
    websocket.send(JSON.stringify({ type: 'user_info', ...userInfo, start_removal: true }));
  }
}

/**
 * Loads saved form data from localStorage.
 */
function loadFormData() {
  const saved = localStorage.getItem('optx_form_data');
  if (saved) {
    const data = JSON.parse(saved);
    Object.keys(data).forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = data[id];
    });
  }
}

/**
 * Saves current form data to localStorage.
 */
function saveFormData() {
  const data = {};
  const inputs = document.querySelectorAll('.settings-section input, .settings-section select');
  inputs.forEach(el => {
    if (el.id) data[el.id] = el.value;
  });
  localStorage.setItem('optx_form_data', JSON.stringify(data));
}

/*============================================================================
   NETWORKING & COMMUNICATIONS
   Manages the WebSocket link to the backend Python server.
============================================================================*/

/**
 * Initializes the WebSocket tunnel for real-time agent feedback.
 */
function connectToBackend() {
  const status = document.getElementById('connectionStatus');
  if (status) { status.textContent = 'Connecting...'; status.classList.remove('connected', 'error'); }
  try {
    websocket = new WebSocket('ws://localhost:3000/ws');
    websocket.onopen = () => {
      isBackendConnected = true;
      if (status) { status.textContent = 'Connected'; status.classList.add('connected'); }
    };
    websocket.onmessage = (e) => handleBackendMessage(JSON.parse(e.data));
    websocket.onclose = () => {
      isBackendConnected = false;
      if (status) { status.textContent = 'Offline'; status.classList.remove('connected'); }
    };
    websocket.onerror = () => {
      isBackendConnected = false;
      if (status) { status.textContent = 'Connection Error'; status.classList.remove('connected', 'error'); }
    };
  } catch (e) {
    if (status) { status.textContent = 'Failed'; status.classList.remove('connected'); }
  }
}

/**
 * Dispatches logic based on messages received from the server (logs, errors, signals).
 */
function handleBackendMessage(data) {
  if (data.type === 'response' || data.type === 'status_update') {
    addLogEntry(data.message, 'system');
  } else if (data.type === 'log') {
    addLogEntry(data.message);
  } else if (data.type === 'error') {
    addLogEntry(`Error: ${data.message}`, 'error');
  } else if (data.type === 'complete') {
    addLogEntry(data.message || 'Automation completed successfully.', 'success');
  } else if (data.type === 'session_ended' || data.type === 'reset_ui') {
    // Reset browser UI on session termination
    const browserView = document.getElementById('browserView');
    if (browserView) browserView.classList.remove('fullscreen');
    const screenshot = document.getElementById('browserScreenshot');
    const placeholder = document.getElementById('browserPlaceholder');
    const liveFrame = document.getElementById('liveBrowserFrame');
    if (screenshot) { screenshot.src = ''; screenshot.classList.add('hidden'); }
    if (liveFrame) { liveFrame.src = ''; liveFrame.classList.add('hidden'); }
    if (placeholder) placeholder.classList.remove('hidden');
    updateBrowserUrl('Ready for automation');
    const statusText = document.getElementById('browserStatusText');
    if (statusText) statusText.textContent = 'Status: Ready';
    if (sessionActive) addLogEntry('Session Closed.', 'system');
    sessionActive = false;
  } else if (data.type === 'browser_update') {
    // Update live preview with new agent status/URL
    sessionActive = true;
    const liveFrame = document.getElementById('liveBrowserFrame');
    if (!liveFrame || liveFrame.classList.contains('hidden')) {
      showBrowserView();
      if (data.url) updateBrowserUrl(data.url);
      if (data.screenshot) updateBrowserScreenshot(data.screenshot);
    }
    // Filter out empty/stale messages to prevent log spam
    if (data.message) {
      const msg = data.message.trim();
      // Skip empty, "Initializing...", or undefined messages
      if (msg && msg !== 'Initializing...' && msg !== 'undefined') {
        const statusText = document.getElementById('browserStatusText');
        if (statusText) statusText.textContent = `Status: ${msg}`;
        addLogEntry(msg);
      }
    }
  }
}

function clearLog() {
  const log = document.getElementById('removalLog');
  if (log) log.innerHTML = '<div class="log-entry system">Log cleared. System ready.</div>';
}

/**
 * Appends a formatted message to the UI activity tracker.
 */
function addLogEntry(message, type = '') {
  const log = document.getElementById('removalLog');
  if (!log) return;
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const now = new Date();
  const timeStr = `${(now.getHours() % 12) || 12}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')} ${now.getHours() >= 12 ? 'PM' : 'AM'}`;
  entry.innerHTML = `<span style="color: var(--text-dim); font-size: 0.7rem; margin-right: 5px;">[${timeStr}]</span> ${message}`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

/**
 * Connects the UI to a live interactive browser stream (if available).
 */
function showLiveBrowser(liveUrl) {
  const content = document.getElementById('browserContent');
  if (!content) return;
  resetEndButton();
  const placeholder = document.getElementById('browserPlaceholder');
  const screenshot = document.getElementById('browserScreenshot');
  if (placeholder) placeholder.classList.add('hidden');
  if (screenshot) screenshot.classList.add('hidden');
  let iframe = document.getElementById('liveBrowserFrame');
  if (!iframe) {
    iframe = document.createElement('iframe');
    iframe.id = 'liveBrowserFrame';
    iframe.className = 'browser-iframe';
    content.appendChild(iframe);
  }
  iframe.src = liveUrl;
  iframe.classList.remove('hidden');
  showBrowserView(true);
  updateBrowserUrl('Live Interactive Browser');
  const statusText = document.getElementById('browserStatusText');
  if (statusText) statusText.textContent = 'Status: Live Interactive';
}

/*============================================================================
   PHONE OSINT ENGINE
   Orchestrates phone metadata lookups and site connectivity verification.
============================================================================*/

function sanitizePhone(input) { return (input || '').replace(/\D+/g, ''); }

/**
 * Standardizes phone numbers into standard (XXX) XXX-XXXX format.
 */
function formatPhone(phone) {
  const digits = sanitizePhone(phone);
  if (digits.length === 10) return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  if (digits.length === 11 && digits[0] === '1') return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  return phone;
}

/**
 * High-performance site checker to verify external targets are online.
 */
async function checkSiteStatus(siteName) {
  try {
    const response = await fetch(`http://localhost:3000/check-site/${encodeURIComponent(siteName)}`, { method: 'GET', signal: AbortSignal.timeout(20000) });
    const data = await response.json();
    return data.online ? 'online' : 'offline';
  } catch (e) { return 'offline'; }
}

async function updateSiteStatus(siteName, rowId) {
  const indicator = document.getElementById(`status-${rowId}`);
  if (!indicator) return;
  const status = await checkSiteStatus(siteName);
  indicator.className = `status-indicator status-${status}`;
  indicator.title = status === 'online' ? 'Online' : 'Offline';
}

/**
 * Builds the data visualization tables for OSINT results.
 */
function buildTable(data, caption, prefix) {
  if (!data.length) return `<h3>${caption}</h3><p>No services found.</p>`;
  let html = `<h3>${caption}</h3><table><thead><tr><th>#</th><th>Site</th><th>Lookup</th><th>Opt-out</th></tr></thead><tbody>`;
  data.forEach((site, i) => {
    html += `<tr><td>${i + 1}</td><td><span id="status-${prefix}-${i}" class="status-indicator status-checking" title="Checking..."></span>${site.name}</td><td><a href="${site.searchUrl}" target="_blank">Lookup</a></td><td>${site.optOutUrl ? `<a href="${site.optOutUrl}" target="_blank" class="optout-link">Opt-out</a>` : 'N/A'}</td></tr>`;
  });
  return html + '</tbody></table>';
}

/**
 * Triggers the main OSINT search flow from the search bar.
 */
function performSearch(evt) {
  evt.preventDefault();
  const phone = sanitizePhone(document.getElementById('phoneInput').value);
  const resultsDiv = document.getElementById('results');
  if (!phone) {
    resultsDiv.innerHTML = '<p>Please enter a valid phone number.</p>';
    return;
  }
  showResults(phone);
}

/**
 * Initializes the results layout for a newly searched phone number.
 */
function showResults(phone) {
  const res = document.getElementById('results');
  if (!phone) { res.innerHTML = '<p>Please enter a valid phone number.</p>'; res.classList.remove('hidden'); return; }
  res.classList.remove('hidden');
  currentPhone = phone;
  const pd = phone.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
  const pp = phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1)$2-$3');
  const updated = sites.map(s => ({ ...s, searchUrl: s.searchUrl.replace('{phone}', phone).replace('{phone_dashes}', pd).replace('{phone_parentheses}', pp) }));
  const fs = updated.filter(s => s.category === 'free');
  const ps = updated.filter(s => s.category === 'paid');
  res.innerHTML = `
    <div id="phoneInfoInline"></div>
    <div class="status-legend">
      <span class="legend-item"><span class="status-indicator status-online"></span> Online</span>
      <span class="legend-item"><span class="status-indicator status-checking"></span> Checking</span>
      <span class="legend-item"><span class="status-indicator status-offline"></span> Offline</span>
    </div>
    <div class="tables-container">
      <div class="table-wrapper">${buildTable(fs, 'Free Sites', 'free')}</div>
      <div class="table-wrapper">${buildTable(ps, 'Paid Sites', 'paid')}</div>
    </div>`;
  fs.forEach((s, i) => updateSiteStatus(s.name, `free-${i}`));
  ps.forEach((s, i) => updateSiteStatus(s.name, `paid-${i}`));
}

/*============================================================================
   INITIALIZATION & BOOTSTRAPPING
   The entry point for application startup. Sets up connectivity and SPA state.
============================================================================*/

document.addEventListener('DOMContentLoaded', () => {
  // Start backend handshake immediately
  connectToBackend();

  // Resolve initial view based on URL hash (default to search)
  const hash = window.location.hash.replace('#', '') || 'search';
  switchView((hash === 'about' || hash === 'removal') ? hash : 'search');

  // Listen for browser navigation (Back/Forward)
  window.onpopstate = () => {
    let freshHash = window.location.hash.replace('#', '') || 'search';
    switchView(freshHash === 'home' ? 'search' : freshHash);
  };

  // Update UI site telemetry
  const sC = document.getElementById('siteCount');
  if (sC) sC.textContent = sites.length;

  // Load saved form data
  loadFormData();

  // Attach auto-save listeners
  document.querySelectorAll('.settings-section input, .settings-section select').forEach(el => {
    el.addEventListener('input', saveFormData);
    el.addEventListener('change', saveFormData);
  });
});