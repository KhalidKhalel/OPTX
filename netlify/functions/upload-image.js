const { Blob } = require('buffer');

const LITTERBOX_UPLOAD_URL = 'https://litterbox.catbox.moe/resources/internals/api.php';
const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;
const DEFAULT_EXPIRATION = '1h';
const ALLOWED_EXPIRATIONS = new Set(['1h', '12h', '24h', '72h']);
const ALLOWED_IMAGE_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp'
]);

function jsonResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store'
    },
    body: JSON.stringify(body)
  };
}

function sanitizeFileName(fileName, contentType) {
  const cleanName = String(fileName || 'upload')
    .replace(/[^a-z0-9._-]/gi, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);

  if (/\.[a-z0-9]{2,5}$/i.test(cleanName)) return cleanName;

  const extension = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp'
  }[contentType] || 'png';

  return `${cleanName || 'upload'}.${extension}`;
}

exports.handler = async event => {
  if (event.httpMethod === 'OPTIONS') {
    return jsonResponse(204, {});
  }

  if (event.httpMethod === 'GET') {
    return jsonResponse(200, { ok: true });
  }

  if (event.httpMethod !== 'POST') {
    return jsonResponse(405, { error: 'Use POST to upload an image.' });
  }

  try {
    const payload = JSON.parse(event.body || '{}');
    const contentType = String(payload.contentType || '').toLowerCase();
    const expiresIn = ALLOWED_EXPIRATIONS.has(payload.expiresIn) ? payload.expiresIn : DEFAULT_EXPIRATION;
    const rawData = String(payload.data || '').replace(/^data:image\/[a-z0-9.+-]+;base64,/i, '');

    if (!ALLOWED_IMAGE_TYPES.has(contentType)) {
      return jsonResponse(400, { error: 'Only JPG, PNG, GIF, and WebP images are supported.' });
    }

    if (!rawData) {
      return jsonResponse(400, { error: 'No image data was provided.' });
    }

    const bytes = Buffer.from(rawData, 'base64');
    if (!bytes.length || bytes.length > MAX_UPLOAD_BYTES) {
      return jsonResponse(400, { error: 'Choose an image smaller than 4 MB.' });
    }

    const formData = new FormData();
    formData.append('reqtype', 'fileupload');
    formData.append('time', expiresIn);
    formData.append('fileToUpload', new Blob([bytes], { type: contentType }), sanitizeFileName(payload.fileName, contentType));

    const uploadResponse = await fetch(LITTERBOX_UPLOAD_URL, {
      method: 'POST',
      body: formData
    });

    const uploadText = (await uploadResponse.text()).trim();
    if (!uploadResponse.ok || !/^https?:\/\//i.test(uploadText)) {
      return jsonResponse(502, { error: uploadText || 'Temporary image upload failed.' });
    }

    return jsonResponse(200, { url: uploadText, expiresIn });
  } catch (error) {
    return jsonResponse(500, { error: error.message || 'Temporary image upload failed.' });
  }
};
