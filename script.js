// OPTX Frontend - static lookup, reverse image search, free scan, removal guide, and about views.

// Core state and limits.
let activeSearchToken = 0;
let activeImagePreviewUrl = '';

const SITE_CHECK_TIMEOUT_MS = 7000;
const SITE_CHECK_CONCURRENCY = 8;
const MAX_REVERSE_IMAGE_BYTES = 4 * 1024 * 1024;
const IMAGE_UPLOAD_ENDPOINT = '/.netlify/functions/upload-image';
const LITTERBOX_DIRECT_UPLOAD_URL = 'https://litterbox.catbox.moe/resources/internals/api.php';
const DEFAULT_LITTERBOX_EXPIRATION = '1h';
const LITTERBOX_EXPIRATIONS = {
  '1h': '1 hour',
  '12h': '12 hours',
  '24h': '1 day',
  '72h': '3 days'
};
const VALID_VIEWS = new Set(['search', 'scan', 'removal', 'about']);
const ACTIVE_LOOKUP_TYPES = new Set(['phone', 'image']);
const APPLE_MAPS_EMAIL = 'MapsImageCollection@apple.com';
const APPLE_MAPS_SUBJECT = 'Privacy Request: Obscure Home Imagery';

const IMAGE_REMOVAL_NOTICE = {
  title: 'Remove It From The Source Site First',
  message: 'This search tool usually does not host the image. Open the lookup results, copy the source page URL where the image appears, then delete it from your account or contact that website/company and ask them to remove it. After the source page is removed, use the search engine removal or refresh tool if the old image still appears.'
};

const REVERSE_IMAGE_PROVIDERS = [
  {
    name: 'TinEye',
    category: 'free',
    mode: 'direct',
    website: 'https://tineye.com',
    optOutUrl: 'https://tineye.com/image_removal',
    url: imageUrl => `https://tineye.com/search?url=${encodeURIComponent(imageUrl)}`
  },
  {
    name: 'Google Lens',
    category: 'free',
    mode: 'direct',
    website: 'https://lens.google.com',
    removalNotice: {
      ...IMAGE_REMOVAL_NOTICE,
      title: 'Google Lens Removal Info',
      learnMoreUrl: 'https://support.google.com/websearch/answer/4628134?hl=en'
    },
    url: imageUrl => `https://lens.google.com/uploadbyurl?url=${encodeURIComponent(imageUrl)}`
  },
  {
    name: 'Bing Visual',
    category: 'free',
    mode: 'direct',
    website: 'https://www.bing.com',
    removalNotice: {
      ...IMAGE_REMOVAL_NOTICE,
      title: 'Bing Visual Search Removal Info',
      learnMoreUrl: 'https://www.bing.com/webmasters/help/content-removal-cb6c294d'
    },
    url: imageUrl => `https://www.bing.com/images/search?view=detailv2&iss=sbi&FORM=SBIIRP&sbisrc=UrlPaste&q=imgurl%3A${encodeURIComponent(imageUrl)}`
  },
  {
    name: 'Yandex',
    category: 'free',
    mode: 'direct',
    website: 'https://yandex.com/images/',
    removalNotice: {
      ...IMAGE_REMOVAL_NOTICE,
      title: 'Yandex Images Removal Info',
      learnMoreUrl: 'https://yandex.com/support/abuse/en/troubleshooting/search/default'
    },
    url: imageUrl => `https://yandex.com/images/search?rpt=imageview&url=${encodeURIComponent(imageUrl)}`
  },
  {
    name: 'FaceCheck.ID',
    category: 'paid',
    mode: 'manual',
    website: 'https://facecheck.id',
    optOutUrl: 'https://facecheck.id/en/RemoveMyPhotos',
    url: 'https://facecheck.id'
  },
  {
    name: 'PicDetective',
    category: 'free',
    mode: 'manual',
    website: 'https://picdetective.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://picdetective.com'
  },
  {
    name: 'RankWatch',
    category: 'free',
    mode: 'manual',
    website: 'https://www.rankwatch.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://www.rankwatch.com/free-tools/reverse-image-search'
  },
  {
    name: 'Artist Ninja',
    category: 'free',
    mode: 'manual',
    website: 'https://artist.ninja',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://artist.ninja/reverse-image-search'
  },
  {
    name: 'Labnol',
    category: 'free',
    mode: 'manual',
    website: 'https://www.labnol.org',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://www.labnol.org/reverse'
  },
  {
    name: 'Reversely.ai',
    category: 'paid',
    mode: 'manual',
    website: 'https://www.reversely.ai',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://www.reversely.ai'
  },
  {
    name: 'Copyseeker',
    category: 'free',
    mode: 'direct',
    website: 'https://copyseeker.net',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: imageUrl => `https://copyseeker.net/search?imageurl=${encodeURIComponent(imageUrl)}`
  },
  {
    name: 'Lenso.ai',
    category: 'paid',
    mode: 'manual',
    website: 'https://lenso.ai',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://lenso.ai/en'
  },
  {
    name: 'DeCopy',
    category: 'free',
    mode: 'manual',
    website: 'https://decopy.ai',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://decopy.ai/reverse-image/'
  },
  {
    name: 'VerifierPro',
    category: 'free',
    mode: 'manual',
    website: 'https://verifierpro.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://verifierpro.com/tools/reverse-image-search/'
  },
  {
    name: 'IntelTechniques Images',
    category: 'free',
    mode: 'manual',
    website: 'https://inteltechniques.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://inteltechniques.com/tools/Images.html'
  },
  {
    name: 'GeoSpy',
    category: 'free',
    mode: 'manual',
    website: 'https://geospy.net',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://geospy.net/en/geospy'
  },
  {
    name: 'GeoSpy Tech',
    category: 'free',
    mode: 'manual',
    website: 'https://geospy.tech',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://geospy.tech/en#upload'
  },
  {
    name: 'Reverse Image Location',
    category: 'free',
    mode: 'manual',
    website: 'https://reverseimagelocation.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://reverseimagelocation.com/tools/geospy-alternative'
  },
  {
    name: 'Raven',
    category: 'paid',
    mode: 'manual',
    website: 'https://www.withraven.ai',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://www.withraven.ai/'
  },
  {
    name: 'Searqle',
    category: 'paid',
    mode: 'manual',
    website: 'https://searqle.com',
    removalNotice: IMAGE_REMOVAL_NOTICE,
    url: 'https://searqle.com/reverse-image-lookup/'
  }
];

// Future lookup types stay configured but disabled in the UI until they are ready.
const LOOKUP_TYPES = {
  phone: {
    label: 'Phone',
    pluralLabel: 'phone lookup',
    fields: [
      {
        key: 'phone',
        label: 'Phone number',
        type: 'tel',
        placeholder: '202-555-0125',
        autocomplete: 'tel',
        inputmode: 'numeric',
        pattern: '[0-9-]*',
        maxlength: 12
      }
    ]
  },
  image: {
    label: 'Image',
    pluralLabel: 'reverse image search',
    fields: [
      { key: 'image', label: 'Image file', type: 'file', accept: 'image/*' },
      {
        key: 'expiresIn',
        label: 'Expire after',
        type: 'select',
        options: [
          { value: '1h', label: '1 hour' },
          { value: '12h', label: '12 hours' },
          { value: '24h', label: '1 day' },
          { value: '72h', label: '3 days' }
        ]
      }
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

function getPhoneEntryDigits(input) {
  const digits = sanitizePhone(input);
  const withoutCountryCode = digits.length > 10 && digits.startsWith('1') ? digits.slice(1) : digits;
  return withoutCountryCode.slice(0, 10);
}

function formatPhoneEntry(input) {
  const digits = getPhoneEntryDigits(input);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
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

  const controls = document.querySelector('.lookup-controls');
  const submitButton = document.querySelector('#lookupForm button[type="submit"]');
  controls?.classList.toggle('lookup-controls-image', type === 'image');
  if (submitButton) {
    const label = type === 'image' ? 'Upload image' : 'Search';
    submitButton.title = label;
    submitButton.setAttribute('aria-label', label);
  }

  container.innerHTML = LOOKUP_TYPES[type].fields.map(field => {
    const fieldLabel = `${field.label}${field.optional ? ' (optional)' : ''}`;
    const fieldId = `lookup-${field.key}`;
    const fieldControl = field.type === 'select'
      ? `<select id="${fieldId}" name="${field.key}" aria-describedby="error-${field.key}">
          ${field.options.map(option => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`).join('')}
        </select>`
      : `<input
          id="${fieldId}"
          name="${field.key}"
          type="${field.type}"
          ${field.placeholder ? `placeholder="${field.placeholder}"` : ''}
          autocomplete="${field.autocomplete || 'off'}"
          aria-describedby="error-${field.key}"
          ${field.optional ? '' : 'aria-required="true"'}
          ${field.accept ? `accept="${field.accept}"` : ''}
          ${field.inputmode ? `inputmode="${field.inputmode}"` : ''}
          ${field.pattern ? `pattern="${field.pattern}"` : ''}
          ${field.maxlength ? `maxlength="${field.maxlength}"` : ''}
        />`;

    return `
      <label class="lookup-field" for="${fieldId}">
        <span>${fieldLabel}</span>
        ${fieldControl}
        <span id="error-${field.key}" class="field-error" aria-live="polite"></span>
      </label>`;
  }).join('');

  if (type === 'phone') setupPhoneInputMask();
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

  if (type === 'image') {
    const file = document.getElementById('lookup-image')?.files?.[0];
    const expiresIn = LITTERBOX_EXPIRATIONS[raw.expiresIn] ? raw.expiresIn : DEFAULT_LITTERBOX_EXPIRATION;
    if (!file) return { error: 'Choose an image first.', field: 'image' };
    if (!file.type.startsWith('image/')) return { error: 'Choose a valid image file.', field: 'image' };
    if (file.size > MAX_REVERSE_IMAGE_BYTES) return { error: 'Choose an image smaller than 4 MB.', field: 'image' };
    return { file, expiresIn };
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

function getPhoneCaretPosition(formatted, digitIndex) {
  if (digitIndex <= 0) return 0;

  let seenDigits = 0;
  for (let i = 0; i < formatted.length; i += 1) {
    if (/\d/.test(formatted[i])) seenDigits += 1;
    if (seenDigits === digitIndex) return i + 1;
  }

  return formatted.length;
}

function formatPhoneInputElement(input) {
  const cursor = input.selectionStart ?? input.value.length;
  const digitsBeforeCursor = getPhoneEntryDigits(input.value.slice(0, cursor)).length;
  const formatted = formatPhoneEntry(input.value);
  const nextCursor = getPhoneCaretPosition(formatted, digitsBeforeCursor);

  input.value = formatted;
  if (document.activeElement === input) {
    input.setSelectionRange(nextCursor, nextCursor);
  }
}

function setupPhoneInputMask() {
  const input = document.getElementById('lookup-phone');
  if (!input) return;

  input.addEventListener('beforeinput', event => {
    if (event.inputType !== 'insertText') return;
    if (event.data && /\D/.test(event.data)) event.preventDefault();
  });

  input.addEventListener('paste', event => {
    event.preventDefault();
    const pasteText = event.clipboardData?.getData('text') || '';
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? start;
    input.value = `${input.value.slice(0, start)}${pasteText}${input.value.slice(end)}`;
    formatPhoneInputElement(input);
  });

  input.addEventListener('input', () => formatPhoneInputElement(input));
}

// Reverse image search.
function setImageStatus(message, type = 'info') {
  const status = document.getElementById('imageUploadStatus');
  if (!status) return;

  status.textContent = message;
  status.className = `image-status image-status-${type}`;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      resolve(result.includes(',') ? result.split(',')[1] : result);
    };
    reader.onerror = () => reject(new Error('Could not read the selected image.'));
    reader.readAsDataURL(file);
  });
}

function getReverseImageProviderUrl(provider, imageUrl) {
  return typeof provider.url === 'function' ? provider.url(imageUrl) : provider.url;
}

function getReverseImageProviderStatusUrl(provider) {
  return provider.statusUrl || provider.website || (typeof provider.url === 'string' ? provider.url : '');
}

function buildInfoButton(notice, fallbackTitle = 'Removal Info') {
  if (!notice) return '';

  return `
    <button
      type="button"
      class="image-removal-info"
      data-title="${escapeHtml(notice.title || fallbackTitle)}"
      data-message="${escapeHtml(notice.message || '')}"
      ${notice.learnMoreUrl ? `data-learn-more-url="${escapeHtml(notice.learnMoreUrl)}"` : ''}
    >Info</button>`;
}

function buildReverseImageOptOut(provider) {
  if (provider.optOutUrl) {
    return `<a href="${escapeHtml(provider.optOutUrl)}" target="_blank" rel="noopener noreferrer" class="optout-link">Opt-out</a>`;
  }

  if (provider.removalNotice) {
    return buildInfoButton(provider.removalNotice, 'Image Removal Info');
  }

  return '<span class="not-available">N/A</span>';
}

function buildReverseImageTable(providers, caption, prefix, imageUrl) {
  if (!providers.length) {
    return `<h3>${escapeHtml(caption)}</h3><p class="empty-state">No reverse image sites found in this group yet.</p>`;
  }

  const rows = providers.map((provider, i) => {
    const rowId = `${prefix}-${i}`;
    const providerUrl = getReverseImageProviderUrl(provider, imageUrl);

    return `
      <tr>
        <td>${i + 1}</td>
        <td class="site-cell">
          <span class="site-cell-content">
            <span id="status-${rowId}" class="inline-status-dot status-checking" aria-label="Checking" title="Checking"></span>
            <span class="site-name">${escapeHtml(provider.name)}</span>
            <span class="mode-letter mode-${provider.mode}" title="${provider.mode === 'direct' ? 'Direct lookup' : 'Manual lookup'}">${provider.mode === 'direct' ? 'D' : 'M'}</span>
          </span>
        </td>
        <td><a href="${escapeHtml(providerUrl)}" target="_blank" rel="noopener noreferrer">Lookup</a></td>
        <td>${buildReverseImageOptOut(provider)}</td>
      </tr>`;
  }).join('');

  return `
    <h3>${escapeHtml(caption)}</h3>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Site</th>
          <th>Lookup</th>
          <th>Opt-out</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function isMissingFunctionError(error) {
  return Boolean(error?.missingFunction || /failed to fetch|load failed|networkerror/i.test(error?.message || ''));
}

function getImageUploadErrorMessage(error) {
  const message = error?.message || '';
  if (/failed to fetch|load failed|networkerror/i.test(message)) {
    return 'Temporary image upload could not connect. No account or API key is needed, but the browser could not reach the upload service.';
  }
  return message || 'The temporary upload failed.';
}

async function uploadImageThroughFunction(file, expiresIn) {
  const data = await fileToBase64(file);
  const response = await fetch(IMAGE_UPLOAD_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fileName: file.name,
      contentType: file.type,
      expiresIn,
      data
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.url) {
    const error = new Error(payload.error || 'The temporary upload failed.');
    error.missingFunction = response.status === 404;
    throw error;
  }

  return payload.url;
}

async function uploadImageDirectly(file, expiresIn) {
  const formData = new FormData();
  formData.append('reqtype', 'fileupload');
  formData.append('time', LITTERBOX_EXPIRATIONS[expiresIn] ? expiresIn : DEFAULT_LITTERBOX_EXPIRATION);
  formData.append('fileToUpload', file, file.name || 'upload.png');

  const response = await fetch(LITTERBOX_DIRECT_UPLOAD_URL, {
    method: 'POST',
    body: formData
  });

  const uploadText = (await response.text()).trim();
  if (!response.ok || !/^https?:\/\//i.test(uploadText)) {
    throw new Error(uploadText || 'Direct Litterbox upload failed.');
  }

  return uploadText;
}

function renderReverseImageResults(imageUrl, file, expiresIn) {
  const results = document.getElementById('results');
  if (!results) return;

  if (activeImagePreviewUrl) URL.revokeObjectURL(activeImagePreviewUrl);
  activeImagePreviewUrl = URL.createObjectURL(file);
  const expirationLabel = LITTERBOX_EXPIRATIONS[expiresIn] || LITTERBOX_EXPIRATIONS[DEFAULT_LITTERBOX_EXPIRATION];
  const freeProviders = REVERSE_IMAGE_PROVIDERS.filter(provider => provider.category === 'free');
  const paidProviders = REVERSE_IMAGE_PROVIDERS.filter(provider => provider.category === 'paid');

  results.classList.remove('hidden');
  results.innerHTML = `
    <div class="image-results">
      <div class="image-results-heading">
        <h2>Reverse Image Search</h2>
        <p class="image-lead">Temporary image URL ready. Open the search tools below.</p>
        <p class="image-manual-note">Some sites may require you to manually upload the image or paste the temporary image URL.</p>
        <p class="image-warning">Warning: the uploaded image becomes a temporary public URL. Do not upload private or sensitive images.</p>
        <p id="imageUploadStatus" class="image-status image-status-success" aria-live="polite">Temporary image URL ready.</p>
      </div>
      <div class="image-result-summary">
        <div class="image-preview-block">
          <span class="image-preview-label">Uploaded image preview</span>
          <a class="image-preview-link" href="${escapeHtml(imageUrl)}" target="_blank" rel="noopener noreferrer" title="Open full image">
            <img src="${activeImagePreviewUrl}" alt="Uploaded image preview" />
          </a>
        </div>
        <div class="image-url-block">
          <span>Temporary image URL</span>
          <a href="${escapeHtml(imageUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(imageUrl)}</a>
          <span class="image-expiration">Expires after ${escapeHtml(expirationLabel)}</span>
          <p class="litterbox-delete-note">Litterbox does not provide an anonymous early-delete endpoint. This temporary image will auto-delete after ${escapeHtml(expirationLabel)}.</p>
          <div class="image-actions">
            <button type="button" class="copy-image-url" data-copy-url="${escapeHtml(imageUrl)}">
              <i class="fa-regular fa-copy" aria-hidden="true"></i>
              <span>Copy URL</span>
            </button>
          </div>
        </div>
      </div>
      <div class="result-summary">
        <span>Image results</span>
        <span>${REVERSE_IMAGE_PROVIDERS.length} reverse image search links</span>
      </div>
    ${buildResultLegend('Direct lookup includes the temporary image URL in the search link.', 'Manual lookup opens the site, then you may need to upload the image or paste the URL there.')}
      <div class="tables-container">
        <div class="table-wrapper">${buildReverseImageTable(freeProviders, 'Free Sites', 'image-free', imageUrl)}</div>
        <div class="table-wrapper">${buildReverseImageTable(paidProviders, 'Paid Sites', 'image-paid', imageUrl)}</div>
      </div>
    </div>`;

  const statusQueue = [
    ...freeProviders.map((provider, i) => ({
      site: { statusUrl: getStatusTarget(getReverseImageProviderStatusUrl(provider)) },
      rowId: `image-free-${i}`
    })),
    ...paidProviders.map((provider, i) => ({
      site: { statusUrl: getStatusTarget(getReverseImageProviderStatusUrl(provider)) },
      rowId: `image-paid-${i}`
    }))
  ];

  runStatusChecks(statusQueue, activeSearchToken);
}

async function copyTemporaryImageUrl(button) {
  const url = button.dataset.copyUrl;
  if (!url) return;

  try {
    await navigator.clipboard.writeText(url);
    button.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i><span>Copied</span>';
    window.setTimeout(() => {
      button.innerHTML = '<i class="fa-regular fa-copy" aria-hidden="true"></i><span>Copy URL</span>';
    }, 1800);
  } catch {
    setImageStatus('Could not copy automatically. Select and copy the temporary URL manually.', 'error');
  }
}

function closeImageRemovalNotice() {
  document.getElementById('imageRemovalModal')?.classList.add('hidden');
}

function showImageRemovalNotice(button) {
  let modal = document.getElementById('imageRemovalModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'imageRemovalModal';
    modal.className = 'image-removal-modal hidden';
    modal.innerHTML = `
      <div class="image-removal-dialog" role="dialog" aria-modal="true" aria-labelledby="imageRemovalTitle">
        <button type="button" class="image-removal-close" aria-label="Close">&times;</button>
        <h3 id="imageRemovalTitle"></h3>
        <p></p>
        <a href="#" target="_blank" rel="noopener noreferrer" class="image-removal-learn">Learn more</a>
      </div>`;
    document.body.appendChild(modal);

    modal.addEventListener('click', event => {
      if (event.target === modal || event.target.closest('.image-removal-close')) {
        closeImageRemovalNotice();
      }
    });
  }

  modal.querySelector('h3').textContent = button.dataset.title || 'Image Removal Info';
  modal.querySelector('p').textContent = button.dataset.message || IMAGE_REMOVAL_NOTICE.message;

  const learnLink = modal.querySelector('.image-removal-learn');
  const learnMoreUrl = button.dataset.learnMoreUrl || '';
  learnLink.classList.toggle('hidden', !learnMoreUrl);
  if (learnMoreUrl) learnLink.href = learnMoreUrl;

  modal.classList.remove('hidden');
  modal.querySelector('.image-removal-close')?.focus();
}

function getTemplateFieldValue(id, fallback) {
  const value = document.getElementById(id)?.value?.trim();
  return value || fallback;
}

function buildAppleMapsEmailBody() {
  const fullName = getTemplateFieldValue('appleMapsFullName', '[Full Name]');
  const address = getTemplateFieldValue('appleMapsAddress', '[Address]');
  const phone = getTemplateFieldValue('appleMapsPhone', '[Phone Number]');

  return `Dear Apple Maps Team,

I am requesting that my home be permanently blurred or obscured from Apple Maps imagery, including the Look Around feature, for privacy reasons.

Property details:
Address: ${address}
Request type: Privacy concern / obscure imagery of my home

Please let me know if you need any documentation or additional information to confirm that I am authorized to make this request.

Thank you,
${fullName}
${phone}`;
}

function updateAppleMapsTemplate() {
  const template = document.getElementById('appleMapsTemplate');
  if (!template) return;

  const body = buildAppleMapsEmailBody();
  template.value = `Subject: ${APPLE_MAPS_SUBJECT}\n\n${body}`;

  const draftLink = document.getElementById('appleMapsDraftLink');
  if (draftLink) {
    draftLink.href = `mailto:${APPLE_MAPS_EMAIL}?subject=${encodeURIComponent(APPLE_MAPS_SUBJECT)}&body=${encodeURIComponent(body)}`;
  }
}

async function copyTemplate(button) {
  const target = document.getElementById(button.dataset.templateTarget);
  if (!target) return;

  try {
    await navigator.clipboard.writeText(target.value);
    const originalText = button.textContent;
    button.textContent = 'Copied';
    window.setTimeout(() => {
      button.textContent = originalText;
    }, 1600);
  } catch {
    target.focus();
    target.select();
  }
}

async function handleReverseImageUpload(evt) {
  if (evt) evt.preventDefault();

  const values = normalizeLookupValues('image');
  const results = document.getElementById('results');

  if (values.error) {
    if (results) {
      results.innerHTML = '';
      results.classList.add('hidden');
    }
    showValidationMessage(values);
    return;
  }

  activeSearchToken += 1;
  const file = values.file;
  const expiresIn = values.expiresIn || DEFAULT_LITTERBOX_EXPIRATION;
  const expirationLabel = LITTERBOX_EXPIRATIONS[expiresIn] || LITTERBOX_EXPIRATIONS[DEFAULT_LITTERBOX_EXPIRATION];

  if (results) {
    results.classList.remove('hidden');
    results.innerHTML = `
      <div class="image-results-heading">
        <h2>Reverse Image Search</h2>
        <p class="image-lead">Upload an image to generate a temporary public image URL and open reverse image search tools.</p>
        <p class="image-warning">Warning: the uploaded image becomes a temporary public URL. Do not upload private or sensitive images.</p>
        <p id="imageUploadStatus" class="image-status image-status-checking" aria-live="polite">Uploading image to a temporary public URL that expires after ${escapeHtml(expirationLabel)}...</p>
      </div>`;
  }

  try {
    let imageUrl;

    try {
      imageUrl = await uploadImageThroughFunction(file, expiresIn);
    } catch (error) {
      if (!isMissingFunctionError(error)) throw error;
      setImageStatus('Local function unavailable. Trying direct Litterbox upload...', 'checking');
      imageUrl = await uploadImageDirectly(file, expiresIn);
    }

    setImageStatus('Temporary image URL ready.', 'success');
    renderReverseImageResults(imageUrl, file, expiresIn);
  } catch (error) {
    setImageStatus(getImageUploadErrorMessage(error), 'error');
  }
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

function getSiteCategory(site, type) {
  return site.categories?.[type] || site.category || 'free';
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
      const optOutTemplate = site.optOutUrls?.[type] || site.optOutUrl;
      const optOutUrl = optOutTemplate ? replaceTokens(optOutTemplate, values) : null;
      const optOutNotice = site.optOutNotices?.[type] || site.optOutNotice;

      return {
        ...site,
        category: getSiteCategory(site, type),
        searchUrl,
        statusUrl,
        optOutUrl,
        optOutNotice,
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
  const isInlineDot = indicator.classList.contains('inline-status-dot');

  const labels = {
    checking: 'Checking',
    online: 'Online',
    offline: 'No response',
    unknown: 'Unconfirmed'
  };

  indicator.className = isInlineDot ? `inline-status-dot status-${status}` : `status-${status}`;
  if (!isInlineDot) indicator.textContent = labels[status];
  indicator.setAttribute('aria-label', labels[status]);
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
      : site.optOutNotice
        ? buildInfoButton(site.optOutNotice, 'Removal Info')
        : '<span class="not-available">N/A</span>';

    return `
      <tr>
        <td>${i + 1}</td>
        <td class="site-cell">
          <span class="site-cell-content">
            <span id="status-${rowId}" class="inline-status-dot status-checking" aria-label="Checking" title="Checking"></span>
            <span class="site-name">${escapeHtml(site.name)}</span>
            <span class="mode-letter mode-${site.lookupMode}" title="${site.lookupMode === 'direct' ? 'Direct lookup' : 'Manual lookup'}">${site.lookupMode === 'direct' ? 'D' : 'M'}</span>
          </span>
        </td>
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
          <th>Lookup</th>
          <th>Opt-out</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function buildResultLegend(directText, manualText) {
  return `
    <div class="status-legend">
      <span class="legend-item"><span class="status-dot legend-online"></span> Online: response received</span>
      <span class="legend-item"><span class="status-dot legend-checking"></span> Checking</span>
      <span class="legend-item"><span class="status-dot legend-unknown"></span> Unconfirmed: browser blocked check</span>
      <span class="legend-item"><span class="status-dot legend-offline"></span> No response: timed out</span>
    </div>
    <div class="lookup-mode-help">
      <span class="mode-help-direct"><strong class="mode-letter mode-direct">D</strong> - ${escapeHtml(directText)}</span>
      <span class="mode-help-manual"><strong class="mode-letter mode-manual">M</strong> - ${escapeHtml(manualText)}</span>
    </div>`;
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
    ${buildResultLegend('Direct lookup includes the phone number in the URL.', 'Manual lookup opens the site, then you may need to enter the number there.')}
    <div class="tables-container">
      <div class="table-wrapper">${buildTable(freeSites, 'Free Sites', 'free')}</div>
      <div class="table-wrapper">${buildTable(paidSites, 'Paid Sites', 'paid')}</div>
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
  if (type === 'image') {
    handleReverseImageUpload();
    return;
  }

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
    const results = document.getElementById('results');
    if (results) {
      results.innerHTML = '';
      results.classList.add('hidden');
    }
  });

  document.getElementById('lookupForm')?.addEventListener('submit', performSearch);
  document.querySelectorAll('[data-template-input]').forEach(input => {
    input.addEventListener('input', updateAppleMapsTemplate);
  });
  document.querySelectorAll('[data-template-target]').forEach(button => {
    button.addEventListener('click', () => copyTemplate(button));
  });
  updateAppleMapsTemplate();

  document.getElementById('results')?.addEventListener('click', event => {
    const copyButton = event.target.closest('.copy-image-url');
    if (copyButton) copyTemporaryImageUrl(copyButton);

    const removalInfoButton = event.target.closest('.image-removal-info');
    if (removalInfoButton) showImageRemovalNotice(removalInfoButton);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeImageRemovalNotice();
  });

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
