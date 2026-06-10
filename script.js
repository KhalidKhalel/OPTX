// OPTX Frontend - static lookup, free scan, removal guide, and about views.

// Core state and limits.
let activeSearchToken = 0;

const SITE_CHECK_TIMEOUT_MS = 7000;
const SITE_CHECK_CONCURRENCY = 8;
const VALID_VIEWS = new Set(['search', 'scan', 'removal', 'about']);
const ACTIVE_LOOKUP_TYPES = new Set(['phone']);

// Future lookup types stay configured but disabled in the UI until they are ready.
const LOOKUP_TYPES = {
  phone: {
    label: 'Phone',
    pluralLabel: 'phone lookup',
    fields: [
      { key: 'phone', label: 'Phone number', type: 'tel', placeholder: '202-555-0125', autocomplete: 'tel' }
    ]
  },
  name: {
    label: 'Name',
    pluralLabel: 'name search',
    fields: [
      { key: 'firstName', label: 'First name', type: 'text', placeholder: 'John', autocomplete: 'given-name' },
      { key: 'lastName', label: 'Last name', type: 'text', placeholder: 'Doe', autocomplete: 'family-name' },
      { key: 'city', label: 'City', type: 'text', placeholder: 'Austin', autocomplete: 'address-level2', optional: true },
      { key: 'state', label: 'State', type: 'text', placeholder: 'TX', autocomplete: 'address-level1', optional: true, maxlength: 2 }
    ]
  },
  email: {
    label: 'Email',
    pluralLabel: 'email lookup',
    fields: [
      { key: 'email', label: 'Email address', type: 'email', placeholder: 'name@example.com', autocomplete: 'email' }
    ]
  },
  vin: {
    label: 'VIN',
    pluralLabel: 'VIN lookup',
    fields: [
      { key: 'vin', label: 'VIN', type: 'text', placeholder: '17-character VIN', autocomplete: 'off', maxlength: 17 }
    ]
  },
  ip: {
    label: 'IP',
    pluralLabel: 'IP lookup',
    fields: [
      { key: 'ip', label: 'IP address', type: 'text', placeholder: '8.8.8.8', autocomplete: 'off' }
    ]
  },
  address: {
    label: 'Address',
    pluralLabel: 'address lookup',
    fields: [
      { key: 'street', label: 'Street address', type: 'text', placeholder: '123 Main St', autocomplete: 'street-address' },
      { key: 'city', label: 'City', type: 'text', placeholder: 'Austin', autocomplete: 'address-level2', optional: true },
      { key: 'state', label: 'State', type: 'text', placeholder: 'TX', autocomplete: 'address-level1', optional: true, maxlength: 2 }
    ]
  }
};

// Input helpers.
function sanitizePhone(input) {
  return (input || '').replace(/\D+/g, '');
}

function normalizePhone(input) {
  const digits = sanitizePhone(input);
  if (digits.length === 11 && digits.startsWith('1')) return digits.slice(1);
  if (digits.length === 10) return digits;
  return null;
}

function formatPhone(phone) {
  const digits = normalizePhone(phone) || sanitizePhone(phone);
  if (digits.length === 10) return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  return phone;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

// Navigation.
function switchView(viewId) {
  const nextView = VALID_VIEWS.has(viewId) ? viewId : 'search';

  document.querySelectorAll('.view-section').forEach(section => {
    section.classList.toggle('hidden', section.id !== `${nextView}View`);
  });

  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.view === nextView);
  });

  document.querySelectorAll('.home-only').forEach(el => {
    el.classList.toggle('hidden', nextView !== 'search');
  });

  document.querySelectorAll('.hide-on-about').forEach(el => {
    el.classList.toggle('hidden', nextView === 'about');
  });

  const results = document.getElementById('results');
  if (results) {
    const hasResults = results.innerHTML.trim() !== '';
    results.classList.toggle('hidden', nextView !== 'search' && hasResults);
  }

  const titles = {
    search: 'OPTX - Search',
    scan: 'OPTX - Free Scan',
    removal: 'OPTX - Removal',
    about: 'OPTX - About'
  };
  document.title = titles[nextView];

  const nextHash = `#${nextView}`;
  if (window.location.hash !== nextHash) {
    window.history.pushState(null, '', nextHash);
  }
}

function getLookupType() {
  const select = document.getElementById('lookupType');
  const type = select?.value || 'phone';
  if (LOOKUP_TYPES[type] && ACTIVE_LOOKUP_TYPES.has(type)) return type;
  if (select) select.value = 'phone';
  return 'phone';
}

// Form rendering and validation.
function renderLookupFields(type = getLookupType()) {
  const container = document.getElementById('lookupFields');
  if (!container) return;

  container.innerHTML = LOOKUP_TYPES[type].fields.map(field => `
    <label class="lookup-field" for="lookup-${field.key}">
      <span>${field.label}${field.optional ? ' (optional)' : ''}</span>
      <input
        id="lookup-${field.key}"
        name="${field.key}"
        type="${field.type}"
        placeholder="${field.placeholder}"
        autocomplete="${field.autocomplete || 'off'}"
        aria-describedby="error-${field.key}"
        ${field.optional ? '' : 'aria-required="true"'}
        ${field.maxlength ? `maxlength="${field.maxlength}"` : ''}
      />
      <span id="error-${field.key}" class="field-error" aria-live="polite"></span>
    </label>
  `).join('');
}

function normalizeLookupValues(type) {
  const raw = {};
  LOOKUP_TYPES[type].fields.forEach(field => {
    raw[field.key] = document.getElementById(`lookup-${field.key}`)?.value?.trim() || '';
  });

  if (type === 'phone') {
    const phone = normalizePhone(raw.phone);
    if (!phone) return { error: 'Enter a valid 10-digit US phone number.', field: 'phone' };
    return { phone };
  }

  if (type === 'name') {
    const firstName = raw.firstName.trim();
    const lastName = raw.lastName.trim();
    if (!firstName) return { error: 'Enter a first name.', field: 'firstName' };
    if (!lastName) return { error: 'Enter a last name.', field: 'lastName' };
    return {
      firstName,
      lastName,
      city: raw.city.trim(),
      state: raw.state.trim().toUpperCase()
    };
  }

  if (type === 'email') {
    const email = raw.email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return { error: 'Enter a valid email address.', field: 'email' };
    return { email };
  }

  if (type === 'vin') {
    const vin = raw.vin.replace(/[^a-z0-9]/gi, '').toUpperCase();
    if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) {
      return { error: 'Enter a valid 17-character VIN. VINs do not use I, O, or Q.', field: 'vin' };
    }
    return { vin };
  }

  if (type === 'ip') {
    const ip = raw.ip.trim();
    const ipv4 = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;
    const ipv6 = /^[0-9a-f:]{2,}$/i;
    if (!ipv4.test(ip) && !ipv6.test(ip)) return { error: 'Enter a valid IPv4 or IPv6 address.', field: 'ip' };
    return { ip };
  }

  if (type === 'address') {
    const street = raw.street.trim();
    if (!street) return { error: 'Enter a street address.', field: 'street' };
    return {
      street,
      city: raw.city.trim(),
      state: raw.state.trim().toUpperCase()
    };
  }

  return { error: 'Unsupported lookup type.' };
}

function clearValidationMessages() {
  document.querySelectorAll('.lookup-field').forEach(field => field.classList.remove('has-error'));
  document.querySelectorAll('.lookup-field input').forEach(input => input.removeAttribute('aria-invalid'));
  document.querySelectorAll('.field-error').forEach(error => {
    error.textContent = '';
  });
}

function showValidationMessage(error) {
  if (!error.field) return;
  const input = document.getElementById(`lookup-${error.field}`);
  const field = input?.closest('.lookup-field');
  const fieldError = document.getElementById(`error-${error.field}`);

  field?.classList.add('has-error');
  input?.setAttribute('aria-invalid', 'true');
  if (fieldError) fieldError.textContent = error.error;
  input?.focus();
}

// URL generation.
function buildReplacementValues(values) {
  const phone = values.phone || '';
  const phoneDashes = phone.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
  const phoneOneDashes = phone.replace(/(\d{3})(\d{3})(\d{4})/, '1-$1-$2-$3');
  const phoneParentheses = phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1)$2-$3');
  const phoneArea = phone.slice(0, 3);
  const phonePrefix = phone.slice(3, 6);
  const fullName = [values.firstName, values.lastName].filter(Boolean).join(' ');
  const address = [values.street, values.city, values.state].filter(Boolean).join(', ');
  const query = [fullName, address, values.email, values.phone, values.vin, values.ip].filter(Boolean).join(' ');

  return {
    phone,
    phone_dashes: phoneDashes,
    phone_1_dashes: phoneOneDashes,
    phone_parentheses: phoneParentheses,
    phone_area: phoneArea,
    phone_prefix: phonePrefix,
    first: values.firstName || '',
    last: values.lastName || '',
    city: values.city || '',
    state: values.state || '',
    name: fullName,
    name_dashes: fullName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    email: values.email || '',
    vin: values.vin || '',
    ip: values.ip || '',
    street: values.street || '',
    address,
    query
  };
}

function replaceTokens(url, values) {
  const replacements = buildReplacementValues(values);
  return url.replace(/\{([a-z0-9_]+)\}/g, (_, key) => encodeURIComponent(replacements[key] ?? ''));
}

function getSiteTypes(site) {
  if (Array.isArray(site.lookupTypes)) return site.lookupTypes;
  if (site.urls) return Object.keys(site.urls);
  return [];
}

function getSiteHomepageUrl(site) {
  return site.website || `https://${site.name}/`;
}

function getSiteLookupConfig(site, type) {
  const url = site.urls?.[type] || (getSiteTypes(site).includes(type) ? site.searchUrl : null);
  if (!url) return null;

  const mode = site.modes?.[type] || (site.manualTypes?.includes(type) || site.manual ? 'manual' : 'direct');
  const statusUrl = site.statusUrls?.[type] || site.statusUrl || getSiteHomepageUrl(site);
  const statusExact = Boolean(site.statusExact || site.statusExactTypes?.includes(type));

  return { url, mode, statusUrl, statusExact };
}

function getStatusTarget(statusUrl) {
  try {
    const parsed = new URL(statusUrl);
    return `${parsed.protocol}//${parsed.host}/`;
  } catch {
    return statusUrl;
  }
}

function prepareSites(type, values) {
  const seen = new Set();

  return sites
    .filter(site => getSiteTypes(site).includes(type))
    .map(site => {
      const lookup = getSiteLookupConfig(site, type);
      if (!lookup) return null;
      const searchUrl = replaceTokens(lookup.url, values);
      const rawStatusUrl = replaceTokens(lookup.statusUrl, values);
      const statusUrl = lookup.statusExact ? rawStatusUrl : getStatusTarget(rawStatusUrl);
      const optOutUrl = site.optOutUrl ? replaceTokens(site.optOutUrl, values) : null;

      return {
        ...site,
        searchUrl,
        statusUrl,
        optOutUrl,
        lookupMode: lookup.mode
      };
    })
    .filter(Boolean)
    .filter(site => {
      const key = site.name.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

// Browser-side status checks only test reachability, not whether a site has a match.
async function fetchWithTimeout(url, method) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), SITE_CHECK_TIMEOUT_MS);

  try {
    await fetch(url, {
      method,
      mode: 'no-cors',
      cache: 'no-store',
      redirect: 'follow',
      signal: controller.signal
    });
    return 'online';
  } catch (error) {
    return error.name === 'AbortError' ? 'offline' : 'unknown';
  } finally {
    window.clearTimeout(timeout);
  }
}

function getFaviconStatusUrl(url) {
  try {
    const parsed = new URL(url);
    return `${parsed.protocol}//${parsed.host}/favicon.ico`;
  } catch {
    return '';
  }
}

function imageWithTimeout(url) {
  if (!url) return Promise.resolve('unknown');

  return new Promise(resolve => {
    const image = new Image();
    const timeout = window.setTimeout(() => {
      image.onload = null;
      image.onerror = null;
      resolve('offline');
    }, SITE_CHECK_TIMEOUT_MS);

    image.onload = () => {
      window.clearTimeout(timeout);
      resolve('online');
    };

    image.onerror = () => {
      window.clearTimeout(timeout);
      resolve('unknown');
    };

    image.referrerPolicy = 'no-referrer';
    image.src = `${url}${url.includes('?') ? '&' : '?'}_=${Date.now()}`;
  });
}

async function checkSiteStatus(url) {
  const headStatus = await fetchWithTimeout(url, 'HEAD');
  if (headStatus === 'online' || headStatus === 'offline') return headStatus;

  const getStatus = await fetchWithTimeout(url, 'GET');
  if (getStatus === 'online' || getStatus === 'offline') return getStatus;

  return imageWithTimeout(getFaviconStatusUrl(url));
}

function setSiteStatus(rowId, status) {
  const indicator = document.getElementById(`status-${rowId}`);
  if (!indicator) return;

  const labels = {
    checking: 'Checking',
    online: 'Online',
    offline: 'No response',
    unknown: 'Unconfirmed'
  };

  indicator.className = `status-pill status-${status}`;
  indicator.innerHTML = `<span class="status-dot"></span>${labels[status]}`;
  indicator.title = status === 'online'
    ? 'The site responded to this browser check.'
    : status === 'offline'
      ? 'The site did not respond before the timeout.'
      : 'The browser could not confirm this site. It may still be online.';
}

async function updateSiteStatus(site, rowId, searchToken) {
  if (site.statusOverride) {
    setSiteStatus(rowId, site.statusOverride);
    return;
  }

  const status = await checkSiteStatus(site.statusUrl);
  if (searchToken !== activeSearchToken) return;
  setSiteStatus(rowId, status);
}

async function runStatusChecks(queue, searchToken) {
  let nextIndex = 0;

  async function worker() {
    while (nextIndex < queue.length && searchToken === activeSearchToken) {
      const item = queue[nextIndex];
      nextIndex += 1;
      await updateSiteStatus(item.site, item.rowId, searchToken);
    }
  }

  const workerCount = Math.min(SITE_CHECK_CONCURRENCY, queue.length);
  await Promise.all(Array.from({ length: workerCount }, worker));
}

// Results rendering.
function buildTable(data, caption, prefix) {
  if (!data.length) {
    return `<h3>${escapeHtml(caption)}</h3><p class="empty-state">No services found for this lookup type yet.</p>`;
  }

  const rows = data.map((site, i) => {
    const rowId = `${prefix}-${i}`;
    const optOut = site.optOutUrl
      ? `<a href="${site.optOutUrl}" target="_blank" rel="noopener noreferrer" class="optout-link">Opt-out</a>`
      : '<span class="not-available">N/A</span>';
    const modeLabel = site.lookupMode === 'manual' ? '<span class="mode-badge">Manual</span>' : '<span class="mode-badge direct">Direct</span>';

    return `
      <tr>
        <td>${i + 1}</td>
        <td class="site-cell">
          <span>${escapeHtml(site.name)}</span>
          ${modeLabel}
        </td>
        <td><span id="status-${rowId}" class="status-pill status-checking"><span class="status-dot"></span>Checking</span></td>
        <td><a href="${site.searchUrl}" target="_blank" rel="noopener noreferrer">Lookup</a></td>
        <td>${optOut}</td>
      </tr>`;
  }).join('');

  return `
    <h3>${escapeHtml(caption)}</h3>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Site</th>
          <th>Status</th>
          <th>Lookup</th>
          <th>Opt-out</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function summarizeLookup(type, values) {
  if (type === 'phone') return formatPhone(values.phone);
  if (type === 'name') return [values.firstName, values.lastName, values.city, values.state].filter(Boolean).join(' ');
  if (type === 'email') return values.email;
  if (type === 'vin') return values.vin;
  if (type === 'ip') return values.ip;
  if (type === 'address') return [values.street, values.city, values.state].filter(Boolean).join(', ');
  return '';
}

function showResults(type, values) {
  const results = document.getElementById('results');
  const searchToken = activeSearchToken + 1;
  activeSearchToken = searchToken;

  const updatedSites = prepareSites(type, values);
  const freeSites = updatedSites.filter(site => site.category === 'free');
  const paidSites = updatedSites.filter(site => site.category === 'paid');
  const typeConfig = LOOKUP_TYPES[type];

  results.classList.remove('hidden');
  results.innerHTML = `
    <div class="result-summary">
      <span>${escapeHtml(typeConfig.label)} results for ${escapeHtml(summarizeLookup(type, values))}</span>
      <span>${updatedSites.length} ${escapeHtml(typeConfig.pluralLabel)} links</span>
    </div>
    <div class="status-legend">
      <span class="legend-item"><span class="status-dot legend-online"></span> Online: response received</span>
      <span class="legend-item"><span class="status-dot legend-checking"></span> Checking</span>
      <span class="legend-item"><span class="status-dot legend-unknown"></span> Unconfirmed: browser blocked check</span>
      <span class="legend-item"><span class="status-dot legend-offline"></span> No response: timed out</span>
    </div>
    <div class="lookup-mode-help">
      <span class="mode-help-direct"><strong>Direct</strong> links include the phone number in the URL.</span>
      <span class="mode-help-manual"><strong>Manual</strong> links open the site, then you may need to enter the number there.</span>
    </div>
    <div class="tables-container">
      <div class="table-wrapper">${buildTable(freeSites, `Free ${typeConfig.label} Sites`, 'free')}</div>
      <div class="table-wrapper">${buildTable(paidSites, `Paid ${typeConfig.label} Sites`, 'paid')}</div>
    </div>`;

  const statusQueue = [
    ...freeSites.map((site, i) => ({ site, rowId: `free-${i}` })),
    ...paidSites.map((site, i) => ({ site, rowId: `paid-${i}` }))
  ];

  runStatusChecks(statusQueue, searchToken);
}

// Event wiring.
function performSearch(evt) {
  evt.preventDefault();
  clearValidationMessages();

  const type = getLookupType();
  const values = normalizeLookupValues(type);
  const results = document.getElementById('results');

  if (values.error) {
    results.innerHTML = '';
    results.classList.add('hidden');
    showValidationMessage(values);
    return;
  }

  showResults(type, values);
}

document.addEventListener('DOMContentLoaded', () => {
  const lookupType = document.getElementById('lookupType');
  renderLookupFields();

  lookupType?.addEventListener('change', () => {
    lookupType.value = getLookupType();
    renderLookupFields(getLookupType());
    clearValidationMessages();
    document.getElementById('results').innerHTML = '';
  });

  document.getElementById('lookupForm')?.addEventListener('submit', performSearch);

  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => switchView(link.dataset.view));
  });

  const hash = window.location.hash.replace('#', '') || 'search';
  switchView(VALID_VIEWS.has(hash) ? hash : 'search');

  window.addEventListener('popstate', () => {
    const nextHash = window.location.hash.replace('#', '') || 'search';
    switchView(VALID_VIEWS.has(nextHash) ? nextHash : 'search');
  });
});
