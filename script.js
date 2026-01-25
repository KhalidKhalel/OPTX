// OSINT Assistant - Frontend
let lastLoggedUrl = '';
let lastLogMessage = '';

// Sites Database is now in sites.js

// Settings
const defaultSettings = { provider: 'api', apiKey: '', llmUrl: 'http://localhost:11434', model: 'llama3.2' };
let appSettings = { ...defaultSettings };
let websocket = null;
let sessionActive = false; // tracks if a browser session is active
let currentPhone = null;

// No colorization/typing needed for simple display

function loadSettings() {
  const saved = localStorage.getItem('appSettings');
  if (saved) appSettings = { ...defaultSettings, ...JSON.parse(saved) };
  applySettingsToUI();
  loadBrowserSettings();
  loadPersonalInfo();
}

function loadPersonalInfo() {
  const saved = localStorage.getItem('optx_user_info');
  if (saved) {
    try {
      const info = JSON.parse(saved);
      if (document.getElementById('userFirstName')) document.getElementById('userFirstName').value = info.first_name || '';
      if (document.getElementById('userLastName')) document.getElementById('userLastName').value = info.last_name || '';
      if (document.getElementById('userEmail')) document.getElementById('userEmail').value = info.email || '';
      if (document.getElementById('userPhone')) document.getElementById('userPhone').value = info.phone || '';
      if (document.getElementById('userStreet')) document.getElementById('userStreet').value = info.street || '';
      if (document.getElementById('userCity')) document.getElementById('userCity').value = info.city || '';
      if (document.getElementById('userState')) document.getElementById('userState').value = info.state || '';
      if (document.getElementById('userZip')) document.getElementById('userZip').value = info.zip || '';
      if (document.getElementById('userDOB')) document.getElementById('userDOB').value = info.dob || '';
      if (document.getElementById('userAge')) document.getElementById('userAge').value = info.age || '';
    } catch (e) {
      console.error('Failed to load personal info:', e);
    }
  }
}

function loadBrowserSettings() {
  const saved = localStorage.getItem('optx_browser_settings');
  const currentProvider = localStorage.getItem('optx_browser_provider') || 'api';

  if (saved) {
    try {
      const allSettings = JSON.parse(saved);
      // Support legacy single-object format and new nested format
      if (allSettings.api || allSettings.local) {
        browserSettings = { ...browserSettings, ...allSettings };
      } else {
        // Migration: put old settings into both slots
        browserSettings.api = { ...allSettings };
        browserSettings.local = { ...allSettings };
      }

      // Apply settings based on CURRENT provider
      const settings = browserSettings[currentProvider];
      if (document.getElementById('stealthMode')) document.getElementById('stealthMode').checked = settings.stealth ?? true;
      if (document.getElementById('autoCaptcha')) {
        const checked = settings.captcha ?? (currentProvider === 'api');
        document.getElementById('autoCaptcha').checked = checked;
        toggleWitAiInput(checked);
      }
      if (document.getElementById('residentialProxy')) document.getElementById('residentialProxy').checked = settings.proxy ?? true;
      if (document.getElementById('humanLikeMode')) document.getElementById('humanLikeMode').checked = settings.humanlike ?? true;
      if (document.getElementById('adblockMode')) document.getElementById('adblockMode').checked = settings.adblock ?? true;
    } catch (e) {
      console.error('Failed to load browser settings:', e);
    }
  }

  // Ensure Wit.ai visibility is synced if no settings saved
  if (!saved) {
    toggleWitAiInput(document.getElementById('autoCaptcha')?.checked ?? false);
  }

  // Load browser API keys
  // Load browserless API key
  const browserlessKey = localStorage.getItem('optx_browserless_key');
  if (browserlessKey && document.getElementById('browserlessKey')) {
    document.getElementById('browserlessKey').value = browserlessKey;
  }
}

function applySettingsToUI() {
  const apiRadio = document.querySelector('input[value="api"]');
  const localRadio = document.querySelector('input[value="local"]');

  if (appSettings.provider === 'api') {
    if (apiRadio) apiRadio.checked = true;
    showApiSettings();
  } else {
    if (localRadio) localRadio.checked = true;
    showLocalSettings();
  }

  if (document.getElementById('apiKey')) document.getElementById('apiKey').value = appSettings.apiKey;
  if (document.getElementById('llmUrl')) document.getElementById('llmUrl').value = appSettings.llmUrl;
  if (document.getElementById('modelName')) document.getElementById('modelName').value = appSettings.modelName || 'google/gemini-2.0-flash-exp:free';
  if (document.getElementById('modelSelect')) document.getElementById('modelSelect').value = appSettings.model;
}

function saveSettings() {
  const apiKey = document.getElementById('apiKey')?.value || '';
  const chatbotApiKey = document.getElementById('chatbotApiKey')?.value || '';
  const modelName = document.getElementById('browserUseModel')?.value || 'gpt-4o-mini';
  const localModel = document.getElementById('modelSelect')?.value || 'llama3.2';

  // Browser API keys
  // Browser API key
  const browserlessKey = document.getElementById('browserlessKey')?.value || '';

  // Browser settings
  // The saveSettings function will now save the entire nested browserSettings object
  // which is updated in real-time by updateBrowserSetting anyway, but we sync UI here too.
  const currentProvider = localStorage.getItem('optx_browser_provider') || 'api';
  browserSettings[currentProvider] = {
    stealth: document.getElementById('stealthMode')?.checked ?? true,
    captcha: document.getElementById('autoCaptcha')?.checked ?? (currentProvider === 'api'),
    proxy: document.getElementById('residentialProxy')?.checked ?? true,
    humanlike: document.getElementById('humanLikeMode')?.checked ?? true,
    adblock: document.getElementById('adblockMode')?.checked ?? true
  };

  // Personal Info
  const userInfo = {
    first_name: document.getElementById('userFirstName')?.value || '',
    last_name: document.getElementById('userLastName')?.value || '',
    email: document.getElementById('userEmail')?.value || '',
    phone: document.getElementById('userPhone')?.value || '',
    street: document.getElementById('userStreet')?.value || '',
    city: document.getElementById('userCity')?.value || '',
    state: document.getElementById('userState')?.value || '',
    zip: document.getElementById('userZip')?.value || '',
    dob: document.getElementById('userDOB')?.value || '',
    age: document.getElementById('userAge')?.value || ''
  };

  // Save settings to localStorage
  localStorage.setItem('optx_browser_settings', JSON.stringify(browserSettings));
  localStorage.setItem('optx_browserless_key', browserlessKey);
  localStorage.setItem('optx_user_info', JSON.stringify(userInfo));

  // Use modelName for API providers, localModel for Ollama
  const finalModel = appSettings.provider === 'api' ? modelName : localModel;
  const statusEl = document.getElementById('settingsStatus');
  const saveBtn = document.querySelector('.save-btn');

  // Save to backend
  fetch('http://localhost:3000/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      chatbot_api_key: chatbotApiKey,
      chatbot_model: 'llama3.1-8b',
      model: finalModel,
      browser_settings: browserSettings[currentProvider], // Only send current provider settings to backend
      browserless_key: browserlessKey,
      wit_ai_token: document.getElementById('witAiToken')?.value || '',
      user_info: userInfo
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        // Add saved animation to button
        if (saveBtn) {
          saveBtn.classList.add('saved');
          saveBtn.textContent = 'Saved!';
          setTimeout(() => {
            saveBtn.classList.remove('saved');
            saveBtn.textContent = 'Save';
          }, 1500);
        }
        statusEl.textContent = 'Settings saved!';
        statusEl.className = 'settings-status success';
        setTimeout(() => closeSettings(), 1000);
        connectToBackend();
      } else {
        statusEl.textContent = 'Error saving settings';
        statusEl.className = 'settings-status error';
      }
    })
    .catch(() => {
      localStorage.setItem('optx_provider', provider);
      localStorage.setItem('optx_api_key', apiKey);
      localStorage.setItem('optx_model', finalModel);
      statusEl.textContent = 'Saved locally (backend not running)';
      statusEl.className = 'settings-status success';
      setTimeout(() => closeSettings(), 1000);
    });
}

function switchView(viewId) {
  // Hide all views
  document.querySelectorAll('.view-section').forEach(section => {
    section.classList.add('hidden');
  });

  // Show selected view
  const targetView = document.getElementById(viewId + 'View');
  if (targetView) {
    targetView.classList.remove('hidden');
  }

  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    const linkText = link.textContent.toLowerCase();
    // Handle "Search" mapping to "home" view
    const matchesView = linkText === viewId.toLowerCase() ||
      (linkText === 'search' && viewId === 'home');
    if (matchesView) {
      link.classList.add('active');
    }
  });

  // Update page title and URL hash
  const titles = {
    'home': 'OPTX - OSINT Assistant',
    'removal': 'OPTX - Data Removal',
    'protect': 'OPTX - Protect Your Privacy',
    'sources': 'OPTX - Data Sources',
    'about': 'OPTX - About'
  };
  document.title = titles[viewId] || 'OPTX - OSINT Assistant';
  // Use #search for the home view, otherwise use the viewId
  const urlHash = viewId === 'home' ? 'search' : viewId;
  window.history.pushState(null, '', '#' + urlHash);

  // Show/hide home-only elements (tagline and warning)
  document.querySelectorAll('.home-only').forEach(el => {
    if (viewId === 'home') {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });

  // Hide elements with 'hide-on-about' class only on About page
  document.querySelectorAll('.hide-on-about').forEach(el => {
    if (viewId === 'about') {
      el.classList.add('hidden');
    } else {
      el.classList.remove('hidden');
    }
  });

  // If going back home, ensure results are visible if they exist
  if (viewId === 'home') {
    const results = document.getElementById('results');
    if (results && results.innerHTML.trim() !== '') {
      results.classList.remove('hidden');
    }
    // Also show phone info if it was visible
    const phoneInfo = document.getElementById('phoneInfoPanel');
    if (phoneInfo && phoneInfo.dataset.wasVisible === 'true') {
      phoneInfo.classList.remove('hidden');
    }
  } else {
    // Hide results and panels when not on home
    const results = document.getElementById('results');
    if (results) results.classList.add('hidden');
    const phoneInfo = document.getElementById('phoneInfoPanel');
    if (phoneInfo) {
      phoneInfo.dataset.wasVisible = (!phoneInfo.classList.contains('hidden')).toString();
      phoneInfo.classList.add('hidden');
    }
  }
}

function updateApiPlaceholder() {
  const provider = document.getElementById('apiProvider')?.value;
  const input = document.getElementById('apiKey');
  const hint = document.getElementById('apiKeyHint');
  const modelNameGroup = document.getElementById('modelNameGroup');
  const browserUseModelGroup = document.getElementById('browserUseModelGroup');
  if (!input) return;

  const placeholders = {
    'openrouter': 'sk-or-v1-xxxxx...',
    'browser-use': 'bu-xxxxx...'
  };
  input.placeholder = placeholders[provider] || 'xxxxx...';

  // Update API key hint link based on provider
  if (hint) {
    const links = {
      'openrouter': { url: 'https://openrouter.ai/keys', text: 'Get free API key from OpenRouter' },
      'browser-use': { url: 'https://cloud.browser-use.com/new-api-key', text: 'Get API key from Browser-Use (1000 free)' }
    };
    const link = links[provider] || links['openrouter'];
    hint.innerHTML = `<i class="fas fa-external-link-alt"></i> <a href="${link.url}" target="_blank">${link.text}</a>`;
  }

  // Toggle between model text input (OpenRouter) and dropdown (Browser-Use)
  if (provider === 'browser-use') {
    if (modelNameGroup) modelNameGroup.classList.add('hidden');
    if (browserUseModelGroup) browserUseModelGroup.classList.remove('hidden');
  } else {
    if (modelNameGroup) modelNameGroup.classList.remove('hidden');
    if (browserUseModelGroup) browserUseModelGroup.classList.add('hidden');
  }
}

function toggleApiKeyVisibility(btn) {
  // If no button passed, use the main apiKey input
  let input, icon;
  if (!btn || btn === window) {
    input = document.getElementById('apiKey');
    icon = document.getElementById('apiKeyEyeIcon');
  } else {
    // Get input from the button's parent container
    input = btn.closest('.input-with-actions').querySelector('input');
    icon = btn.querySelector('i');
  }
  if (!input || !icon) return;

  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }

  // Refocus input to maintain outline if it was focused
  if (document.activeElement === input) {
    input.focus();
  }
}

function updateWitAiLabel(provider) {
  const label = document.getElementById('witAiLabel');
  const dynamicText = document.getElementById('witAiDynamicText');
  const hint = document.getElementById('witAiHint');

  if (provider === 'api') {
    if (label) label.textContent = 'Wit.ai Server Token (Optional Backup)';
    if (dynamicText) dynamicText.style.display = 'block';
  } else {
    if (label) label.textContent = 'Wit.ai Server Token';
    if (dynamicText) dynamicText.style.display = 'none';
  }
}

// NOTE: toggleKeyVisibility REMOVED - use toggleApiKeyVisibility instead

// Browser settings storage - nested per provider
let browserSettings = {
  api: { stealth: true, captcha: true, proxy: true, humanlike: true, adblock: true },
  local: { stealth: true, captcha: false, proxy: true, humanlike: true, adblock: true }
};

function updateBrowserSetting(setting, value) {
  const currentProvider = localStorage.getItem('optx_browser_provider') || 'api';
  browserSettings[currentProvider][setting] = value;
  localStorage.setItem('optx_browser_settings', JSON.stringify(browserSettings));
  console.log(`Browser setting [${currentProvider}] updated: ${setting} = ${value}`);

  // Special handling for CAPTCHA toggle visibility
  if (setting === 'captcha') {
    toggleWitAiInput(value);
  }
}

function toggleWitAiInput(visible) {
  const group = document.getElementById('witAiInputGroup');
  if (group) {
    if (visible) {
      group.classList.remove('hidden');
      const provider = localStorage.getItem('optx_browser_provider') || 'api';
      updateWitAiLabel(provider);
    } else {
      group.classList.add('hidden');
    }
  }
}

// Switch browser provider and show/hide relevant features
function switchBrowserProvider(provider) {
  const browserlessFeatures = document.getElementById('browserlessFeatures');

  if (provider === 'browserless') {
    browserlessFeatures?.classList.remove('hidden');
  }

  // Save provider preference
  localStorage.setItem('optx_browser_provider', provider);
  console.log(`Browser provider switched to: ${provider}`);
}

function copyApiKey(btn) {
  // Get input from button's parent container (works for all API key inputs)
  const inputContainer = btn.closest('.input-with-actions');
  const input = inputContainer ? inputContainer.querySelector('input') : document.getElementById('apiKey');

  if (!input || !input.value) return;

  navigator.clipboard.writeText(input.value).then(() => {
    // Add copied class for SVG animation
    btn.classList.add('copied');

    // Reset after animation
    setTimeout(() => {
      btn.classList.remove('copied');
    }, 1000);
  });
}

function updateProvider(provider) {
  appSettings.provider = provider;
  provider === 'api' ? showApiSettings() : showLocalSettings();
}

function showApiSettings() {
  document.getElementById('apiSettings')?.classList.remove('hidden');
  document.getElementById('localSettings')?.classList.add('hidden');
}

function showLocalSettings() {
  document.getElementById('apiSettings')?.classList.add('hidden');
  document.getElementById('localSettings')?.classList.remove('hidden');
}

function updateBrowserProvider(provider) {
  // Update card styles
  document.getElementById('browserApiCard')?.classList.toggle('active', provider === 'api');
  document.getElementById('browserLocalCard')?.classList.toggle('active', provider === 'local');

  // Show/Hide sections
  const apiKeysSection = document.getElementById('browserApiKeysSection');
  const proxyItem = document.getElementById('proxyToggleItem');
  const adblockItem = document.getElementById('adblockToggleItem');

  if (provider === 'local') {
    apiKeysSection?.classList.add('hidden');
    proxyItem?.classList.add('hidden');
    adblockItem?.classList.add('hidden');

    // Sync UI with LOCAL settings
    const settings = browserSettings.local;
    if (stealth) stealth.checked = settings.stealth;
    if (human) human.checked = settings.humanlike;
    if (captcha) {
      captcha.checked = settings.captcha;
      toggleWitAiInput(settings.captcha);
    }
  } else {
    apiKeysSection?.classList.remove('hidden');
    proxyItem?.classList.remove('hidden');
    adblockItem?.classList.remove('hidden');

    // Sync UI with API settings
    const settings = browserSettings.api;
    if (stealth) stealth.checked = settings.stealth;
    if (human) human.checked = settings.humanlike;
    if (captcha) {
      captcha.checked = settings.captcha;
      toggleWitAiInput(settings.captcha);
    }
  }

  // Store the setting
  localStorage.setItem('optx_browser_provider', provider);

  // Update labels for Wit.ai if visible
  const captchaVisible = document.getElementById('autoCaptcha')?.checked;
  if (captchaVisible) {
    updateWitAiLabel(provider);
  }
}


// Modal Handling
function openSettings() { document.getElementById('settingsModal').classList.add('open'); }
function closeSettings() { document.getElementById('settingsModal').classList.remove('open'); }

function switchSettingsTab(tabName) {
  // Remove active from all tabs and content
  document.querySelectorAll('.settings-tab').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.settings-tab-content').forEach(content => content.classList.remove('active'));

  // Add active to selected tab and content
  const tabButton = document.querySelector(`.settings-tab[onclick*="${tabName}"]`);
  if (tabButton) tabButton.classList.add('active');

  const tabContentId = {
    'ai': 'aiSettingsTab',
    'browser': 'browserSettingsTab'
  }[tabName];

  const tabContent = document.getElementById(tabContentId);
  if (tabContent) tabContent.classList.add('active');
}

document.getElementById('settingsBtn')?.addEventListener('click', openSettings);

window.addEventListener('click', (e) => {
  if (e.target === document.getElementById('settingsModal')) closeSettings();
  if (e.target === document.getElementById('optOutModal')) {
    document.getElementById('optOutModal').classList.remove('open');
    document.getElementById('optOutModal').style.display = 'none';
  }
});

// Chat
function toggleChat() { document.getElementById('chatPanel').classList.toggle('open'); }

document.getElementById('chatBtn')?.addEventListener('click', toggleChat);

function handleChatKeypress(e) { if (e.key === 'Enter') sendMessage(); }

// Handle keydown for Shift+Enter (new line) and Enter (send)
function handleChatKeydown(e) {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      // Shift+Enter: allow default behavior (new line in textarea)
      return;
    } else {
      // Enter without Shift: send message
      e.preventDefault();
      sendMessage();
    }
  }
}

function sendMessage() {


  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  addUserMessage(message);
  input.value = '';
  processUserMessage(message);
}

function addUserMessage(text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message user';
  div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addBotMessage(text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message bot';
  // Check if this is a CAPTCHA warning - apply special styling
  const isCaptcha = text.toLowerCase().includes('captcha detected');
  // Convert newlines to <br> for proper rendering
  const formatted = text.replace(/\n/g, '<br>');
  const contentClass = isCaptcha ? 'message-content captcha-warning' : 'message-content';
  div.innerHTML = `<div class="${contentClass}">${formatted}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function addThinkingIndicator() {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message bot thinking-message';
  div.innerHTML = '<div class="message-content"><div class="thinking"><span></span><span></span><span></span></div></div>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function removeThinkingIndicator() {
  const el = document.querySelector('.thinking-message');
  if (el) el.remove();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Browser View
function showBrowserView(shouldSwitch = false) {
  const browserView = document.getElementById('browserView');
  if (browserView && shouldSwitch) {
    switchView('removal');
  }

  // Show the End button when browser view is shown
  resetEndButton();

  // Try to show the browser-use-webui iframe
  const iframe = document.getElementById('browserUseIframe');
  const placeholder = document.getElementById('browserPlaceholder');
  const screenshot = document.getElementById('browserScreenshot');

  // Check if browser-use-webui is running on port 7788
  if (iframe) {
    // Show iframe, hide placeholder
    iframe.classList.remove('hidden');
    placeholder.classList.add('hidden');
    screenshot.classList.add('hidden');

    // Update URL bar
    document.getElementById('browserUrl').textContent = 'browser-use AI Agent (with element highlighting)';
  }
}

function closeBrowserView() {
  document.getElementById('browserView').classList.add('hidden');
  document.getElementById('browserView').classList.remove('fullscreen');

  // Reset iframe to placeholder
  const iframe = document.getElementById('browserUseIframe');
  const placeholder = document.getElementById('browserPlaceholder');
  if (iframe) iframe.classList.add('hidden');
  if (placeholder) placeholder.classList.remove('hidden');
}

function updateBrowserUrl(url) {
  document.getElementById('browserUrl').textContent = url;
}

function updateBrowserScreenshot(base64Data) {
  const screenshot = document.getElementById('browserScreenshot');
  const placeholder = document.getElementById('browserPlaceholder');
  const iframe = document.getElementById('browserUseIframe');

  if (base64Data) {
    // If we have screenshot data, show screenshot instead of iframe
    screenshot.src = 'data:image/png;base64,' + base64Data;
    screenshot.classList.remove('hidden');
    placeholder.classList.add('hidden');
    if (iframe) iframe.classList.add('hidden');

    // Show End button when screenshots are being displayed
    resetEndButton();
  }
}


function toggleBrowserFullscreen() {
  const browserView = document.getElementById('browserView');
  browserView.classList.toggle('fullscreen');

  const btn = document.querySelector('.browser-expand-btn i');
  if (browserView.classList.contains('fullscreen')) {
    btn.className = 'fas fa-compress';
  } else {
    btn.className = 'fas fa-expand';
  }
}

// Session Control
function endSession() {
  console.log('[OPTX] End button clicked');

  // Send end_session to backend to stop cloud automation
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    console.log('[OPTX] Sending end_session to backend');
    websocket.send(JSON.stringify({ type: 'end_session' }));
  }

  // Keep browser view visible but reset to ready state
  const browserView = document.getElementById('browserView');
  if (browserView) {
    browserView.classList.remove('fullscreen');
  }

  // Reset browser content to placeholder
  const screenshot = document.getElementById('browserScreenshot');
  const placeholder = document.getElementById('browserPlaceholder');
  const liveFrame = document.getElementById('liveBrowserFrame');

  if (screenshot) {
    screenshot.src = '';
    screenshot.classList.add('hidden');
  }
  if (liveFrame) {
    liveFrame.src = '';
    liveFrame.classList.add('hidden');
  }
  if (placeholder) placeholder.classList.remove('hidden');

  // Reset status text to ready state
  const statusText = document.getElementById('browserStatusText');
  if (statusText) statusText.textContent = 'Status: Use chat to start removal';

  // Reset URL bar to ready state
  const urlBar = document.getElementById('browserUrl');
  if (urlBar) urlBar.textContent = 'Ready for automation';

  sessionActive = false;
  addLogEntry('Session ended.', 'system');
  console.log('[OPTX] Session ended - browser reset to ready state');
}




// Show and reset end button when new session starts
function resetEndButton() {
  const endBtn = document.getElementById('endSessionBtn');
  if (endBtn) {
    endBtn.innerHTML = '<i class="fas fa-times"></i> End';
    endBtn.disabled = false;
    endBtn.classList.remove('ended');
    endBtn.classList.remove('hidden'); // Show the button
  }
}





function toggleUserControl() {

  const btn = document.getElementById('takeControlBtn');
  const btnText = document.getElementById('controlBtnText');

  userHasControl = !userHasControl;

  if (userHasControl) {
    btn.classList.add('active');
    btnText.textContent = 'Resume AI';
    sendControlCommand('pause');
  } else {
    btn.classList.remove('active');
    btnText.textContent = 'Take Control';
    sendControlCommand('resume');
  }
}

function sendControlCommand(action) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({ type: 'control', action }));
  }
}

// Message Processing - All messages go to AI now (no hardcoded responses)
function processUserMessage(message) {
  if (isConnected) {
    sendToBackend(message);
  } else {
    addBotMessage('Not connected to backend. The server is not running.\n\nTo start the server:\n1. Open a terminal in the project folder\n2. Run: make run\n\nThis will start the server at localhost:3000');
  }
}


function initiateRemoval() {
  // Save latest info from dashboard fields before starting
  const userInfo = {
    first_name: document.getElementById('userFirstName')?.value || '',
    last_name: document.getElementById('userLastName')?.value || '',
    email: document.getElementById('userEmail')?.value || '',
    phone: document.getElementById('userPhone')?.value || '',
    street: document.getElementById('userStreet')?.value || '',
    city: document.getElementById('userCity')?.value || '',
    state: document.getElementById('userState')?.value || '',
    zip: document.getElementById('userZip')?.value || '',
    dob: document.getElementById('userDOB')?.value || '',
    age: document.getElementById('userAge')?.value || ''
  };
  localStorage.setItem('optx_user_info', JSON.stringify(userInfo));

  addThinkingIndicator();
  showBrowserView(true); // Switch to Removal tab and show sessions
  updateBrowserUrl('Preparing removal process...');

  addLogEntry('Initiating removal process...', 'system');

  // Detailed Identity Logging with placeholders
  const fields = [
    { label: 'First Name', val: userInfo.first_name, key: '{first_name}' },
    { label: 'Last Name', val: userInfo.last_name, key: '{last_name}' },
    { label: 'Email Address', val: userInfo.email, key: '{email}' },
    { label: 'Street Address', val: userInfo.street, key: '{street}' },
    { label: 'City', val: userInfo.city, key: '{city}' },
    { label: 'State', val: userInfo.state, key: '{state}' },
    { label: 'ZIP Code', val: userInfo.zip, key: '{zip}' },
    { label: 'Phone Number', val: userInfo.phone, key: '{phone}' },
    { label: 'Date of Birth', val: userInfo.dob, key: '{dob}' },
    { label: 'Age', val: userInfo.age, key: '{age}' }
  ];

  fields.forEach(f => {
    const displayVal = f.val ? f.val : 'EMPTY';
    addLogEntry(`${f.label}: ${displayVal} (uses ${f.key})`, 'site');
  });

  // Ensure Residential Proxy is on if requested
  const proxyCheckbox = document.getElementById('residentialProxy');
  if (proxyCheckbox && proxyCheckbox.checked) {
    updateBrowserSetting('proxy', true);
  }

  setTimeout(() => {
    removeThinkingIndicator();

    if (!isConnected) {
      addBotMessage(`Ready to remove your data!

To start automatic removal:

1. Start the backend server

2. Configure your API key in Settings

3. Say "remove my data" again

Or click "Opt-out" on each site to remove manually.`);
    } else {
      // Collect latest personal info
      const currentProvider = localStorage.getItem('optx_browser_provider') || 'api';

      // Force current settings update from UI
      const currentSettings = {
        stealth: document.getElementById('stealthMode')?.checked ?? true,
        captcha: document.getElementById('autoCaptcha')?.checked ?? true,
        proxy: document.getElementById('residentialProxy')?.checked ?? false,
        humanlike: document.getElementById('humanLikeMode')?.checked ?? true,
        adblock: document.getElementById('adblockMode')?.checked ?? true
      };
      browserSettings[currentProvider] = currentSettings;

      const userInfo = {
        type: 'user_info',
        first_name: document.getElementById('userFirstName')?.value || '',
        last_name: document.getElementById('userLastName')?.value || '',
        email: document.getElementById('userEmail')?.value || '',
        phone: document.getElementById('userPhone')?.value || '',
        street: document.getElementById('userStreet')?.value || '',
        city: document.getElementById('userCity')?.value || '',
        state: document.getElementById('userState')?.value || '',
        zip: document.getElementById('userZip')?.value || '',
        dob: document.getElementById('userDOB')?.value || '',
        age: document.getElementById('userAge')?.value || ''
      };

      // Send start message with user data, explicit removal trigger, and latest settings
      websocket.send(JSON.stringify({
        ...userInfo,
        browser_settings: currentSettings,
        start_removal: true
      }));
    }
  }, 1000);
}

// WebSocket
function connectToBackend() {
  const status = document.getElementById('connectionStatus');
  if (status) {
    status.textContent = 'Connecting...';
    status.classList.remove('connected');
    status.classList.remove('error');
  }

  try {
    websocket = new WebSocket('ws://localhost:3000/ws');

    websocket.onopen = () => {
      isConnected = true;
      if (status) {
        status.textContent = 'Connected';
        status.classList.add('connected');
      }

      // Collect latest personal info
      const userInfo = {
        first_name: document.getElementById('userFirstName')?.value || '',
        last_name: document.getElementById('userLastName')?.value || '',
        email: document.getElementById('userEmail')?.value || '',
        phone: document.getElementById('userPhone')?.value || '',
        street: document.getElementById('userStreet')?.value || '',
        city: document.getElementById('userCity')?.value || '',
        state: document.getElementById('userState')?.value || '',
        zip: document.getElementById('userZip')?.value || '',
        dob: document.getElementById('userDOB')?.value || '',
        age: document.getElementById('userAge')?.value || ''
      };

      websocket.send(JSON.stringify({
        type: 'config',
        provider: appSettings.provider,
        apiKey: appSettings.apiKey,
        llmUrl: appSettings.llmUrl,
        model: appSettings.model,
        browser_settings: browserSettings[currentProvider],
        user_info: userInfo
      }));
    };

    websocket.onmessage = (e) => handleBackendMessage(JSON.parse(e.data));

    websocket.onclose = () => {
      isConnected = false;
      if (status) {
        status.textContent = 'Offline';
        status.classList.remove('connected');
      }
    };

    websocket.onerror = () => {
      isConnected = false;
      if (status) {
        status.textContent = 'Connection Error';
        status.classList.remove('connected');
        status.classList.add('error');
      }
    };
  } catch (e) {
    if (status) {
      status.textContent = 'Failed';
      status.classList.remove('connected');
    }
  }
}

// Track pending chat timeout
let chatTimeoutId = null;

function sendToBackend(message) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    addThinkingIndicator();

    // Clear any existing timeout
    if (chatTimeoutId) {
      clearTimeout(chatTimeoutId);
    }

    // Set 30-second timeout for response
    chatTimeoutId = setTimeout(() => {
      removeThinkingIndicator();
      addBotMessage('The AI is taking too long to respond. This might be due to rate limits or connection issues. Please try again in a few seconds.');
      chatTimeoutId = null;
    }, 30000);

    websocket.send(JSON.stringify({ type: 'chat', message, phone: currentPhone }));
  }
}

function handleBackendMessage(data) {
  // Clear chat timeout when we receive any response
  if (chatTimeoutId) {
    clearTimeout(chatTimeoutId);
    chatTimeoutId = null;
  }

  removeThinkingIndicator();

  if (data.type === 'response') {
    addBotMessage(data.message);
    addLogEntry(data.message);
  }
  else if (data.type === 'error') {
    addBotMessage(`Error: ${data.message}`);
    addLogEntry(`Error: ${data.message}`, 'error');
  }
  else if (data.type === 'complete') {
    addBotMessage(data.message);
    addLogEntry('Automation completed successfully.', 'success');
  }
  else if (data.type === 'session_ended' || data.type === 'reset_ui') {
    // Session ended by backend - reset browser to ready state (keep visible)
    const browserView = document.getElementById('browserView');
    if (browserView) {
      browserView.classList.remove('fullscreen');
    }

    const screenshot = document.getElementById('browserScreenshot');
    const placeholder = document.getElementById('browserPlaceholder');
    const liveFrame = document.getElementById('liveBrowserFrame');

    if (screenshot) { screenshot.src = ''; screenshot.classList.add('hidden'); }
    if (liveFrame) {
      liveFrame.src = '';
      liveFrame.classList.add('hidden');
    }
    if (placeholder) placeholder.classList.remove('hidden');

    updateBrowserUrl('Ready for automation');
    const statusText = document.getElementById('browserStatusText');
    if (statusText) statusText.textContent = 'Status: Use chat to start removal';

    // Log session end if it was active
    if (sessionActive) {
      addLogEntry('Session ended.', 'system');
    }
    sessionActive = false;
  }
  else if (data.type === 'live_browser') {
    // Show interactive live browser view
    showLiveBrowser(data.live_url);
    addLogEntry('Live browser session started.', 'success');
    sessionActive = true;
  }
  else if (data.type === 'browser_update') {
    // Set session active when we start receiving updates
    sessionActive = true;

    // Only show screenshot if we don't have live browser active
    const liveFrame = document.getElementById('liveBrowserFrame');
    if (!liveFrame || liveFrame.classList.contains('hidden')) {
      showBrowserView();
      if (data.url) {
        updateBrowserUrl(data.url);
        // Only log if URL actually changed to prevent flooding
        if (data.url !== lastLoggedUrl) {
          addLogEntry(`Navigating to: ${data.url}`, 'site');
          lastLoggedUrl = data.url;
        }
      }
      if (data.screenshot) updateBrowserScreenshot(data.screenshot);
    }
    if (data.message) {
      const statusText = document.getElementById('browserStatusText');
      if (statusText) statusText.textContent = `Status: ${data.message}`;

      // Only log significant events and avoid duplicates
      const heartbeatMsgs = ["Working...", "Processing page...", "Thinking..."];
      if (!heartbeatMsgs.includes(data.message) && data.message !== lastLogMessage) {
        addLogEntry(data.message);
        lastLogMessage = data.message;
      }
    }
  }
}

function clearLog() {
  const log = document.getElementById('removalLog');
  if (!log) return;

  log.innerHTML = '<div class="log-entry system">Log cleared. System ready.</div>';
  console.log('[OPTX] Activity log cleared');
}

function addLogEntry(message, type = '') {
  const log = document.getElementById('removalLog');
  if (!log) return;

  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;

  // Add timestamp in 12h format
  const now = new Date();
  let hours = now.getHours();
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const seconds = now.getSeconds().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // the hour '0' should be '12'
  const timeStr = `${hours}:${minutes}:${seconds} ${ampm}`;

  entry.innerHTML = `<span style="color: var(--text-dim); font-size: 0.7rem; margin-right: 5px;">[${timeStr}]</span> ${message}`;

  log.appendChild(entry);

  // Use a slight timeout to ensure DOM is rendered before scrolling
  setTimeout(() => {
    log.scroll({
      top: log.scrollHeight,
      behavior: 'smooth'
    });
  }, 10);
}


function showLiveBrowser(liveUrl) {
  const content = document.getElementById('browserContent');
  if (!content) return;

  // Reset end button for new session
  resetEndButton();


  // Hide placeholder and screenshot
  const placeholder = document.getElementById('browserPlaceholder');
  const screenshot = document.getElementById('browserScreenshot');
  if (placeholder) placeholder.classList.add('hidden');
  if (screenshot) screenshot.classList.add('hidden');

  // Create or show iframe
  let iframe = document.getElementById('liveBrowserFrame');
  if (!iframe) {
    iframe = document.createElement('iframe');
    iframe.id = 'liveBrowserFrame';
    iframe.className = 'browser-iframe';
    content.appendChild(iframe);
  }

  iframe.src = liveUrl;
  iframe.classList.remove('hidden');

  // Show browser view and update status
  showBrowserView(true);
  updateBrowserUrl('Live Interactive Browser');
  const statusText = document.getElementById('browserStatusText');
  if (statusText) statusText.textContent = 'Status: Live Interactive';
}


// Phone Lookup
function sanitizePhone(input) { return (input || '').replace(/\D+/g, ''); }

function formatPhone(phone) {
  if (phone.length === 10) {
    return `(${phone.slice(0, 3)}) ${phone.slice(3, 6)}-${phone.slice(6)}`;
  } else if (phone.length === 11 && phone[0] === '1') {
    return `+1 (${phone.slice(1, 4)}) ${phone.slice(4, 7)}-${phone.slice(7)}`;
  }
  return phone;
}

async function checkSiteStatus(siteName) {
  try {
    // Use backend proxy to check main website (not lookup/optout URLs)
    // 20s timeout to allow backend (15s) to complete slower checks
    const response = await fetch(`http://localhost:3000/check-site/${encodeURIComponent(siteName)}`, {
      method: 'GET',
      signal: AbortSignal.timeout(20000)
    });
    const data = await response.json();
    return data.online ? 'online' : 'offline';
  } catch (e) {
    // Backend unavailable or timeout - return offline (conservative approach)
    return 'offline';
  }
}

async function updateSiteStatus(siteName, rowId) {
  const indicator = document.getElementById(`status-${rowId}`);
  if (!indicator) return;

  const status = await checkSiteStatus(siteName);
  indicator.className = `status-indicator status-${status}`;
  indicator.title = status === 'online' ? 'Online' : 'Offline';
}

function buildTable(data, caption, prefix) {
  if (!data.length) return `<h3>${caption}</h3><p>No services found.</p>`;

  let html = `<h3>${caption}</h3><table><thead><tr><th>#</th><th>Site</th><th>Lookup</th><th>Opt-out</th></tr></thead><tbody>`;
  data.forEach((site, i) => {
    const rowId = `${prefix}-${i}`;
    const emailAttr = site.email ? `data-email="${site.email}"` : '';
    const phoneAttr = site.phone ? `data-phone="${site.phone}"` : '';
    html += `<tr>
      <td>${i + 1}</td>
      <td><span id="status-${rowId}" class="status-indicator status-checking" title="Checking..."></span>${site.name}</td>
      <td><a href="${site.searchUrl}" target="_blank">Lookup</a></td>
      <td>${site.optOutUrl ? `<a href="#" class="optout-link" data-url="${site.optOutUrl}" ${emailAttr} ${phoneAttr}>Opt-out</a>` : 'N/A'}</td>
    </tr>`;
  });
  return html + '</tbody></table>';
}

function performSearch(evt) {
  evt.preventDefault();
  const phone = sanitizePhone(document.getElementById('phoneInput').value);
  const resultsDiv = document.getElementById('results');
  const phoneInfoPanel = document.getElementById('phoneInfoPanel');

  if (!phone) {
    resultsDiv.innerHTML = '<p>Please enter a valid phone number.</p>';
    if (phoneInfoPanel) {
      phoneInfoPanel.classList.add('hidden');
      document.body.appendChild(phoneInfoPanel); // Move back to safety
    }
    return;
  }

  // If searching the same number, don't re-render everything to avoid flicker
  if (currentPhone === phone && !resultsDiv.classList.contains('hidden')) {
    // Just refresh the data
    fetchPhoneInfo(phone);
    return;
  }

  // Safely detach phoneInfoPanel before resultsDiv is wiped by showResults
  if (phoneInfoPanel) {
    phoneInfoPanel.classList.add('hidden');
    document.body.appendChild(phoneInfoPanel);
  }

  // Show site results
  showResults(phone);

  // Fetch and display phone carrier/CNAM info
  fetchPhoneInfo(phone);
}

// Phone Lookup - Fetch carrier and CNAM data from free APIs
async function fetchPhoneInfo(phone) {
  // Wait a tiny bit for results to render first
  await new Promise(r => setTimeout(r, 50));

  const phoneInfoPanel = document.getElementById('phoneInfoPanel');
  const inlineContainer = document.getElementById('phoneInfoInline');

  // Move panel content into results section on every search to ensure visibility
  if (inlineContainer && phoneInfoPanel) {
    inlineContainer.appendChild(phoneInfoPanel);
  }

  // Ensure panel is visible
  phoneInfoPanel.classList.remove('hidden');

  // If panel is already visible and we're just refreshing, don't wipe everything to avoid flicker
  if (currentPhone !== phone) {
    // Set all fields to loading placeholder (consistent dash)
    const loadingIds = [
      'callerIdName', 'carrierName', 'ocnInfo', 'lineType',
      'rateCenterName', 'stateInfo', 'lataInfo', 'switchInfo',
      'npaInfo', 'nxxInfo', 'blockDigitInfo', 'coordsInfo', 'statusInfo',
      'voipInfo', 'validNumberInfo', 'inServiceInfo',
      'switchTypeInfo', 'lastVerifiedInfo', 'smsGatewayInfo', 'mmsGatewayInfo',
      'effectiveDateInfo'
    ];
    loadingIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '—';
    });
    // Hide ported section initially
    // Let portedSection remain visible like other boxes
  }

  try {
    // Add cache-busting and force use_llm=false for detailed summary
    const timestamp = Date.now();
    const response = await fetch(`http://localhost:3000/phone-lookup/${phone}?_=${timestamp}&use_llm=false`, {
      cache: 'no-store',
      headers: { 'Cache-Control': 'no-cache' }
    });
    const result = await response.json();

    if (result.ok && result.data) {
      displayPhoneInfo(result.data);
    } else {
      displayPhoneError('Could not fetch phone info');
    }
  } catch (error) {
    console.error('Phone lookup error:', error);
    displayPhoneError('Backend not available - start the server on port 3000');
  }
}

function fetchExplanation(term) {
  fetch(`http://localhost:3000/explain?term=${encodeURIComponent(term)}`)
    .then(r => r.json())
    .then(data => {
      alert(`${data.term}: ${data.explanation}`);
    })
    .catch(err => {
      console.error('Explain fetch error:', err);
      alert('Failed to fetch explanation');
    });
}

function displayPhoneInfo(data) {
  // Caller ID Name
  const callerIdName = data.caller_id?.name;
  const callerIdNote = data.caller_id?.note;
  if (callerIdName) {
    document.getElementById('callerIdName').textContent = callerIdName;
  } else {
    document.getElementById('callerIdName').textContent = 'Feature Coming Soon';
    document.getElementById('callerIdName').title = callerIdNote || 'Caller ID requires carrier database access';
  }

  // Source link for CNAM (optional element)
  const cnamSourceLink = document.getElementById('cnamSourceLink');
  if (cnamSourceLink && data.caller_id?.source?.url) {
    cnamSourceLink.href = data.caller_id.source.url;
  }

  // Carrier - show friendly name if available, otherwise legal name
  const carrierFriendly = data.carrier?.carrier_friendly;
  const carrierLegal = data.carrier?.carrier || 'Not available';
  const carrierEl = document.getElementById('carrierName');
  if (carrierFriendly && carrierFriendly !== carrierLegal) {
    carrierEl.innerHTML = `<strong>${carrierFriendly}</strong> <span style="color:#888;font-size:0.8em;">(${carrierLegal.replace(/, LLC.*$/, '').replace(/ - [A-Z]{2}$/, '')})</span>`;
  } else {
    carrierEl.textContent = carrierLegal;
  }

  // Source link for carrier (optional element)
  const carrierSourceLink = document.getElementById('carrierSourceLink');
  if (carrierSourceLink && data.carrier?.source?.url) {
    carrierSourceLink.href = data.carrier.source.url;
  }

  // OCN
  const ocn = data.carrier?.ocn || '—';
  document.getElementById('ocnInfo').textContent = ocn;

  // Switch Type
  const switchType = data.carrier?.switch_type || '—';
  document.getElementById('switchTypeInfo').textContent = switchType;


  // Effective Date
  const effectiveDateEl = document.getElementById('effectiveDateInfo');
  const effectiveDate = data.carrier?.effective_date;
  if (effectiveDateEl) {
    if (effectiveDate) {
      const eDate = new Date(effectiveDate);
      effectiveDateEl.textContent = eDate.toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      });
    } else {
      effectiveDateEl.textContent = '—';
    }
  }

  // Last Verified
  const lastVerified = data.carrier?.last_verified;
  if (lastVerified) {
    // Format date nicely
    const date = new Date(lastVerified);
    document.getElementById('lastVerifiedInfo').textContent = date.toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  } else {
    document.getElementById('lastVerifiedInfo').textContent = '—';
  }

  // Is Wireless
  const isWirelessEl = document.getElementById('isWirelessInfo');
  if (isWirelessEl) {
    const isWireless = data.carrier?.is_wireless_detected ?? data.carrier?.is_wireless;
    if (isWireless === true) {
      isWirelessEl.textContent = 'Yes';
      isWirelessEl.style.color = '#10b981';  // Green
    } else if (isWireless === false) {
      isWirelessEl.textContent = 'No';
      isWirelessEl.style.color = '#ef4444';  // Red
    } else {
      isWirelessEl.textContent = '—';
      isWirelessEl.style.color = '';
    }
  }

  // SMS Gateway
  const smsGatewayEl = document.getElementById('smsGatewayInfo');
  if (smsGatewayEl) {
    const smsGateway = data.carrier?.sms_gateway;
    if (smsGateway) {
      const phone = data.phone?.number || '';
      smsGatewayEl.textContent = phone + smsGateway;
      smsGatewayEl.style.color = '#00ff88';  // Green = available
    } else {
      smsGatewayEl.textContent = 'N/A';
      smsGatewayEl.style.color = '#888';
    }
  }

  // MMS Gateway
  const mmsGatewayEl = document.getElementById('mmsGatewayInfo');
  if (mmsGatewayEl) {
    const mmsGateway = data.carrier?.mms_gateway;
    if (mmsGateway) {
      const phone = data.phone?.number || '';
      mmsGatewayEl.textContent = phone + mmsGateway;
      mmsGatewayEl.style.color = '#00ff88';  // Green = available
    } else {
      mmsGatewayEl.textContent = 'N/A';
      mmsGatewayEl.style.color = '#888';
    }
  }

  // Line Type
  const lineType = data.carrier?.line_type || '—';
  document.getElementById('lineType').textContent = lineType;

  // VoIP detection
  const isVoip = data.carrier?.is_voip;
  if (isVoip) {
    document.getElementById('voipInfo').textContent = 'Yes';
    document.getElementById('voipInfo').style.color = '#10b981';  // Green
  } else {
    document.getElementById('voipInfo').textContent = 'No';
    document.getElementById('voipInfo').style.color = '#ef4444';  // Red
  }

  // Phone Location (Rate Center + State combined)
  const rateCenter = data.carrier?.rate_center || '';
  const state = data.carrier?.state || '';
  const location = rateCenter && state ? `${rateCenter.toUpperCase()}, ${state}` : (rateCenter || state || '—');
  document.getElementById('rateCenterName').textContent = location;

  // State - show full state name
  const STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
    "PR": "Puerto Rico", "VI": "Virgin Islands", "GU": "Guam"
  };
  const fullStateName = STATE_NAMES[state.trim().toUpperCase()] || state || '—';
  document.getElementById('stateInfo').textContent = fullStateName;

  // Valid Number
  const validNumberEl = document.getElementById('validNumberInfo');
  if (validNumberEl) {
    // Number is valid if we got carrier data back
    const isValid = data.carrier?.carrier || data.carrier?.rate_center;
    if (isValid) {
      validNumberEl.textContent = 'Yes';
      validNumberEl.style.color = '#10b981';  // Green
    } else {
      validNumberEl.textContent = '—';
      validNumberEl.style.color = '#888';
    }
  }

  // LATA
  const lata = data.carrier?.lata || '—';
  document.getElementById('lataInfo').textContent = lata;

  // Switch/CLLI
  const switchClli = data.carrier?.switch_clli || '—';
  document.getElementById('switchInfo').textContent = switchClli;

  // NPA (Area Code) - separate field
  const npa = data.phone?.area_code || '';
  const npaEl = document.getElementById('npaInfo');
  if (npaEl) npaEl.textContent = npa || '—';

  // NXX (Prefix) - separate field
  const nxx = data.phone?.prefix || '';
  const nxxEl = document.getElementById('nxxInfo');
  if (nxxEl) nxxEl.textContent = nxx || '—';

  // Block digit - separate field
  let blockDigit = '';
  const tb = data.carrier?.thousands_block;
  if (typeof tb === 'object' && tb !== null) {
    blockDigit = tb.x || '';
  } else if (typeof tb === 'string' || typeof tb === 'number') {
    blockDigit = String(tb);
  } else if (data.phone?.line) {
    blockDigit = data.phone.line[0] || '';
  }
  const blockDigitEl = document.getElementById('blockDigitInfo');
  if (blockDigitEl) blockDigitEl.textContent = blockDigit || '—';

  // Coordinates
  const coords = data.carrier?.coordinates;
  if (coords && coords.lat && coords.lon) {
    document.getElementById('coordsInfo').textContent = `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`;
  } else {
    document.getElementById('coordsInfo').textContent = '—';
  }

  // Status
  const status = data.carrier?.status || '—';
  document.getElementById('statusInfo').textContent = status;

  // In Service (in Identity section)
  const inServiceEl = document.getElementById('inServiceInfo');
  if (inServiceEl) {
    // Number is in service if we have valid carrier data from LCG
    const hasCarrier = data.carrier?.carrier || data.carrier?.carrier_friendly;
    const hasStatus = data.carrier?.status;
    if (hasCarrier && hasStatus !== 'Disconnected') {
      inServiceEl.textContent = 'Yes';
      inServiceEl.style.color = '#10b981';  // Green
    } else if (hasStatus === 'Disconnected') {
      inServiceEl.textContent = 'No';
      inServiceEl.style.color = '#ef4444';  // Red
    } else {
      inServiceEl.textContent = '—';
      inServiceEl.style.color = '#888';
    }
  }

  // Ported section - only show if ported, with "Ported From" info
  const isPorted = data.carrier?.is_ported;
  // Ported section - always visible, update content
  const portedFromEl = document.getElementById('portedFromInfo');

  if (portedFromEl) {
    const isPorted = data.carrier?.is_ported;
    const ilec = data.carrier?.ilec_name || '';

    if (isPorted && ilec) {
      portedFromEl.textContent = ilec;
    } else {
      portedFromEl.textContent = '—';
    }
  }
}


function displayPhoneError(message) {
  // All fields show placeholder dash
  const ids = [
    'callerIdName', 'lineType', 'voipInfo', 'validNumberInfo', 'inServiceInfo',
    'carrierName', 'ocnInfo', 'switchTypeInfo', 'smsGatewayInfo', 'mmsGatewayInfo', 'lastVerifiedInfo',
    'rateCenterName', 'stateInfo', 'lataInfo', 'coordsInfo',
    'npaInfo', 'nxxInfo', 'blockDigitInfo', 'switchInfo', 'statusInfo'
  ];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = '—';
  });
  document.getElementById('callerIdName').textContent = 'Feature Coming Soon';
  // Hide ported section
  // Porting info remains visible with dash
}

function formatPhoneNumber(phone) {
  // Format as (XXX) XXX-XXXX
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  } else if (digits.length === 11 && digits.startsWith('1')) {
    return `(${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  }
  return phone;
}

function showResults(phone) {
  const resultsDiv = document.getElementById('results');

  if (!phone) {
    resultsDiv.innerHTML = '<p>Please enter a valid phone number.</p>';
    resultsDiv.classList.remove('hidden');
    return;
  }

  resultsDiv.classList.remove('hidden');
  currentPhone = phone;

  // Format phone for different URL formats
  const phoneDashes = phone.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');  // xxx-xxx-xxxx
  const phoneParentheses = phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1)$2-$3');  // (xxx)xxx-xxxx

  // Update URLs - support multiple phone formats
  const updated = sites.map(s => ({
    ...s,
    searchUrl: s.searchUrl
      .replace('{phone}', phone)
      .replace('{phone_dashes}', phoneDashes)
      .replace('{phone_parentheses}', phoneParentheses)
  }));

  const freeSites = updated.filter(s => s.category === 'free');
  const paidSites = updated.filter(s => s.category === 'paid');

  // Insert phone info panel placeholder inside results
  resultsDiv.innerHTML = `
    <h2 class="results-heading"><span class="results-label">Results for</span> <span class="results-phone">${formatPhone(phone)}</span></h2>
    <div id="phoneInfoInline"></div>
    <div class="status-legend">
      <span class="legend-item"><span class="status-indicator status-online"></span> Online</span>
      <span class="legend-item"><span class="status-indicator status-checking"></span> Checking</span>
      <span class="legend-item"><span class="status-indicator status-offline"></span> Offline</span>
    </div>
    <div class="tables-container">
      <div class="table-wrapper">${buildTable(freeSites, 'Free Sites', 'free')}</div>
      <div class="table-wrapper">${buildTable(paidSites, 'Paid Sites', 'paid')}</div>
    </div>`;

  document.querySelectorAll('.optout-link').forEach(a => {
    a.onclick = e => {
      e.preventDefault();
      const siteData = {
        email: a.dataset.email || null,
        phone: a.dataset.phone || null
      };
      openOptOutModal(a.dataset.url, siteData);
    };
  });

  freeSites.forEach((s, i) => updateSiteStatus(s.name, `free-${i}`));
  paidSites.forEach((s, i) => updateSiteStatus(s.name, `paid-${i}`));
}

// Removal is now handled via Chat ONLY

// Opt-Out Modal
const modal = document.getElementById('optOutModal');
const closeBtn = document.querySelector('#optOutModal .close-button');
const modalLink = document.getElementById('modalOptOutLink');
const modalEmail = document.getElementById('modalEmail');
const modalPhone = document.getElementById('modalPhone');

function openOptOutModal(url, site = null) {
  modalLink.href = url;

  // Display contact info from site if available (always show row, just show N/A if not available)
  if (site && site.email) {
    modalEmail.innerHTML = `<a href="mailto:${site.email}">${site.email}</a>`;
  } else {
    modalEmail.textContent = 'N/A';
  }

  if (site && site.phone) {
    modalPhone.innerHTML = `<a href="tel:${site.phone}">${site.phone}</a>`;
  } else {
    modalPhone.textContent = 'N/A';
  }

  modal.style.display = 'flex';
  modal.classList.add('open');
}

closeBtn?.addEventListener('click', () => {
  modal.style.display = 'none';
  modal.classList.remove('open');
});

// Init
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  connectToBackend();

  // Initial view based on hash
  const hash = window.location.hash.replace('#', '');
  if (hash === 'sources' || hash === 'about' || hash === 'protect') {
    switchView(hash);
  } else {
    // #search or empty or #home all go to home view
    switchView('home');
  }

  // Handle back/forward buttons
  window.onpopstate = () => {
    let freshHash = window.location.hash.replace('#', '') || 'home';
    // Map #search to home view
    if (freshHash === 'search') freshHash = 'home';
    switchView(freshHash);
  };

  // Update site count dynamically
  const siteCountEl = document.getElementById('siteCount');
  if (siteCountEl) {
    siteCountEl.textContent = sites.length;
  }

  // Fetch and display current model from backend
  fetchCurrentModel();
});

async function fetchCurrentModel() {
  const modelDisplay = document.getElementById('currentModelDisplay');
  const modelSource = document.getElementById('modelSource');

  if (!modelDisplay) return;

  try {
    const res = await fetch('/api/config');
    const data = await res.json();

    if (data.model && data.model !== 'Not configured') {
      // Remove loading animation
      modelDisplay.classList.remove('loading-dots');
      // Set model name
      modelDisplay.textContent = data.model;
      // Set link to OpenRouter
      modelDisplay.href = `https://openrouter.ai/${data.model}`;
      // Show source
      if (modelSource) {
        modelSource.textContent = '';
      }
    } else {
      modelDisplay.classList.remove('loading-dots');
      modelDisplay.textContent = 'Not configured';
      modelDisplay.removeAttribute('href');
    }
  } catch (e) {
    console.log('Could not fetch current model:', e);
    modelDisplay.classList.remove('loading-dots');
    modelDisplay.textContent = 'Error loading';
    modelDisplay.removeAttribute('href');
  }
}

// Floating Chat Button - Show when scrolling past original button
document.addEventListener('DOMContentLoaded', function () {
  const originalChatBtn = document.getElementById('chatBtn');
  const floatingChatBtn = document.getElementById('floatingChatBtn');

  if (!originalChatBtn || !floatingChatBtn) return;

  window.addEventListener('scroll', function () {
    const btnRect = originalChatBtn.getBoundingClientRect();
    // Show floating button when original is scrolled out of view
    if (btnRect.bottom < 0) {
      floatingChatBtn.classList.add('visible');
    } else {
      floatingChatBtn.classList.remove('visible');
    }
  });
});