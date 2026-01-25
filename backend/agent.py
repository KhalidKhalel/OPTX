"""
OPTX Agent - Backend Server
Consolidated backend logic:
- LLMClient: Unified interface for AI (OpenRouter).
- BrowserlessAgent: Cloud browser automation with CAPTCHA solving.
- TempMail: Verification email handling.
- explain_term: technical term explainer.
- FastAPI Server: Integrated web API.
"""

import asyncio
import os
import base64
import logging
import random
import string
import time
import re
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from openai import OpenAI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Chatbot imports
try:
    from cerebras.cloud.sdk import Cerebras, AsyncCerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False

# CAPTCHA Solver imports
import io
import tempfile
import speech_recognition as sr
from pydub import AudioSegment

# Suppress excessive logging
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Global Constants
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

FORM_SELECTORS = {
    "full_name": ["input[name*='name' i]:not([name*='first' i]):not([name*='last' i])", 
                  "input[id*='name' i]:not([id*='first' i]):not([id*='last' i])", 
                  "#name", "#fullName", "#full_name"],
    "first_name": ["input[name*='first' i]", "input[id*='first' i]", "#firstName", "#first_name", "#fname"],
    "last_name": ["input[name*='last' i]", "input[id*='last' i]", "#lastName", "#last_name", "#lname"],
    "email": ["input[type='email']", "input[name*='email' i]", "#email"],
    "phone": ["input[type='tel']", "input[name*='phone' i]", "#phone"],
    "street": ["input[name*='street' i]", "input[name*='address' i]", "textarea[name*='address' i]", 
               "#address", "#street", "#address1", "#streetAddress"],
    "city": ["input[name*='city' i]", "#city"],
    "zip": ["input[name*='zip' i]", "input[name*='postal' i]", "#zip", "#zipcode", "#postalCode"],
    "state": ["select[name*='state' i]", "select[id*='state' i]", "#state", "select.state", "input[name*='state' i]"]
}

EXTRACTION_PATTERNS = {
    "name": [
        r"(?:my\s+)?name\s+is\s+([A-Za-z]+)\s+([A-Za-z]+)",  
        r"i(?:'m|\s+am)\s+([A-Za-z]+)\s+([A-Za-z]+)", 
        r"^([A-Z][a-z]+)\s+([A-Z][a-z]+)\s*[,\-]",  
        r"^([A-Z][a-z]+)\s+([A-Z][a-z]+)(?:\s|$)", 
    ],
    "street_types": {'st', 'street', 'dr', 'drive', 'ave', 'avenue', 'blvd', 'boulevard', 
                     'rd', 'road', 'ln', 'lane', 'way', 'ct', 'court', 'pl', 'place', 
                     'cir', 'circle', 'apt', 'apartment', 'unit', 'suite', 'ste'},
    "country": [
        r'\n?\s*United\s+States\s*$', r'\n?\s*USA\s*$', 
        r'\n?\s*U\.?S\.?A\.?\s*$', r'\n?\s*US\s*$',
    ],
    "apt_keywords": r'(.*?)(?:\s+)(Apt\.?|Apartment|Unit|Suite|Ste\.?|#)\s*([A-Za-z0-9\-]+)'
}

# === COLORIZED LOGGING ===
# === COLORIZED LOGGING ===
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[0;35m', # Magenta
        'RESET': '\033[0m',
        'BLUE': '\033[0;34m',     # Blue for URLs
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        blue = self.COLORS['BLUE']
        
        # Save original and format levelname (INFO: etc)
        levelname = record.levelname.strip(':').upper()
        record.levelname = f"{color}{levelname}:{reset}"
        
        # Format message and strip any pesky brackets [name] that might be in it
        msg = super().format(record)
        
        # 1. Strip uvicorn-style brackets from the start [uvicorn.error]
        msg = re.sub(r'\[.*?\]\s*', '', msg)
        
        # 2. Colorize Status Codes (e.g. 200, 404)
        msg = re.sub(r'\b(200|201|204)\b', f"{self.COLORS['INFO']}\\1{reset}", msg)
        msg = re.sub(r'\b(404|500)\b', f"{self.COLORS['ERROR']}\\1{reset}", msg)
        
        # 3. Colorize URLs
        msg = re.sub(r'(https?://[^\s]+)', f"{blue}\\1{reset}", msg)
        
        # 4. Clean up any accidental double colons
        msg = msg.replace('::', ':')
        
        record.levelname = levelname # Restore for other potential use
        return msg

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

def setup_all_loggers():
    """Apply the custom formatter to every single logger in the universe."""
    formatter = ColoredFormatter('%(levelname)s %(message)s')
    
    # Root logger
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(logging.StreamHandler())
    for handler in root.handlers:
        handler.setFormatter(formatter)
    
    # All sub-loggers (uvicorn, etc)
    for name in logging.root.manager.loggerDict:
        l = logging.getLogger(name)
        l.propagate = True
        l.handlers = []
        l.level = logging.INFO

setup_all_loggers()

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
ENV_PATH = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=ENV_PATH)

# ============================================================================
# 1. STEALTH MODE - Anti-Detection Evasion Scripts
# ============================================================================

EVASION_SCRIPTS = {
    "webdriver": """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined, configurable: true });
        if (navigator.__proto__) { delete navigator.__proto__.webdriver; }
    """,
    "chrome_runtime": """
        if (!window.chrome) { window.chrome = {}; }
        if (!window.chrome.runtime) { window.chrome.runtime = { onMessage: undefined, onConnect: undefined, sendMessage: function() {} }; }
    """,
    "plugins": """
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ];
                plugins.length = 3;
                plugins.item = (i) => plugins[i] || null;
                plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                plugins.refresh = () => {};
                return plugins;
            },
            configurable: true
        });
    """,
    "languages": """
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'], configurable: true });
        Object.defineProperty(navigator, 'language', { get: () => 'en-US', configurable: true });
    """,
    "permissions": """
        const originalPermissionsQuery = navigator.permissions.query.bind(navigator.permissions);
        navigator.permissions.query = async (parameters) => {
            if (parameters.name === 'notifications') { return { state: Notification.permission, onchange: null }; }
            return originalPermissionsQuery(parameters);
        };
    """,
    "webgl": """
        const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameterOriginal.call(this, parameter);
        };
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const getParameter2Original = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter2Original.call(this, parameter);
            };
        }
    """,
    "hardware_concurrency": """
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8, configurable: true });
    """,
    "platform": """
        Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel', configurable: true });
    """,
    "canvas_noise": """
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (type === 'image/png') {
                const ctx = this.getContext('2d');
                if (ctx) {
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + (Math.random() * 2 - 1)));
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
            }
            return originalToDataURL.apply(this, arguments);
        };
    """,
    "connection": """
        if (navigator.connection) {
            Object.defineProperty(navigator.connection, 'rtt', { get: () => 100, configurable: true });
        }
    """,
    "iframe_contentwindow": """
        const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                const win = originalContentWindow.get.call(this);
                if (win) { try { Object.defineProperty(win.navigator, 'webdriver', { get: () => undefined }); } catch(e) {} }
                return win;
            }
        });
    """,
    "battery": """
        if (navigator.getBattery) {
            navigator.getBattery = async () => ({ charging: true, chargingTime: 0, dischargingTime: Infinity, level: 0.95, addEventListener: () => {}, removeEventListener: () => {} });
        }
    """,
    "notification": """
        if (typeof Notification !== 'undefined') {
            Object.defineProperty(Notification, 'permission', { get: () => 'default', configurable: true });
        }
    """
}

def get_combined_evasion_script(evasions=None):
    """Combine selected evasion scripts into a single script string."""
    if evasions is None:
        evasions = list(EVASION_SCRIPTS.keys())
    scripts = []
    for evasion in evasions:
        if evasion in EVASION_SCRIPTS:
            scripts.append(f"// === {evasion.upper()} EVASION ===")
            scripts.append(EVASION_SCRIPTS[evasion])
    return "\n".join(scripts)

async def _apply_evasions(target, evasions=None):
    """Helper to apply stealth evasions to either a page or context."""
    try:
        script = get_combined_evasion_script(evasions)
        await target.add_init_script(script)
        logger.info(f"Stealth: Applied evasions to {type(target).__name__}")
    except Exception as e:
        logger.error(f"Stealth: Failed to apply evasions: {e}")

async def apply_stealth(page, evasions=None):
    await _apply_evasions(page, evasions)

async def apply_stealth_to_context(context, evasions=None):
    await _apply_evasions(context, evasions)

def get_stealth_launch_args():
    """Get browser launch arguments for stealth mode."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-infobars", "--window-size=1920,1080",
        "--start-maximized", "--no-sandbox",
        "--disable-setuid-sandbox", "--disable-dev-shm-usage",
        "--lang=en-US,en",
    ]

async def verify_stealth(page) -> dict:
    """Verify stealth evasions are working."""
    results = {}
    try:
        webdriver = await page.evaluate("navigator.webdriver")
        results["webdriver"] = "PASS" if webdriver is None or webdriver == False else "FAIL"
        chrome = await page.evaluate("!!window.chrome")
        results["chrome_runtime"] = "PASS" if chrome else "FAIL"
        plugins_count = await page.evaluate("navigator.plugins.length")
        results["plugins"] = "PASS" if plugins_count > 0 else "FAIL"
    except Exception as e:
        results["error"] = str(e)
    return results

# ============================================================================
# 2. HUMAN-LIKE MOUSE & KEYBOARD (Anti-Detection)
# ============================================================================

import math

class HumanMouse:
    """
    Human-like mouse movement and typing for Playwright.
    Uses Bezier curves, variable speed, and random jitter to mimic human behavior.
    Works with any browser agent (HyperAgent or BrowserlessAgent).
    """
    
    def __init__(self, page):
        self.page = page
        self.current_x = 0
        self.current_y = 0
    
    @staticmethod
    def _bezier_curve(p0, p1, p2, p3, steps=50):
        """Generate points along a cubic Bezier curve."""
        points = []
        for i in range(steps + 1):
            t = i / steps
            # Cubic Bezier formula
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            points.append((int(x), int(y)))
        return points
    
    @staticmethod
    def _add_jitter(x, y, intensity=2):
        """Add small random jitter to a point."""
        return (
            x + random.randint(-intensity, intensity),
            y + random.randint(-intensity, intensity)
        )
    
    def _generate_control_points(self, start, end):
        """Generate random control points for Bezier curve."""
        # Distance between points
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Control points with random offset (more curve for longer distances)
        offset = min(distance * 0.3, 100)
        
        cp1 = (
            start[0] + dx * 0.25 + random.uniform(-offset, offset),
            start[1] + dy * 0.25 + random.uniform(-offset, offset)
        )
        cp2 = (
            start[0] + dx * 0.75 + random.uniform(-offset, offset),
            start[1] + dy * 0.75 + random.uniform(-offset, offset)
        )
        
        return cp1, cp2
    
    async def move_to(self, x, y, steps=None):
        """Move mouse to coordinates with human-like Bezier curve."""
        start = (self.current_x, self.current_y)
        end = (x, y)
        
        # Calculate steps based on distance if not provided
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        if steps is None:
            steps = max(20, min(int(distance / 10), 100))
        
        # Generate Bezier curve
        cp1, cp2 = self._generate_control_points(start, end)
        points = self._bezier_curve(start, cp1, cp2, end, steps)
        
        # Move through each point with variable speed
        for i, (px, py) in enumerate(points):
            # Add slight jitter
            jx, jy = self._add_jitter(px, py, intensity=1)
            
            # Variable delay (slower at start/end, faster in middle)
            progress = i / len(points)
            # Ease in-out curve
            speed_factor = 4 * progress * (1 - progress)  # Peaks at 0.5
            delay = 0.005 + (0.015 * (1 - speed_factor))  # 5-20ms
            
            await self.page.mouse.move(jx, jy)
            await asyncio.sleep(delay + random.uniform(0, 0.005))
        
        self.current_x = x
        self.current_y = y
    
    async def click_at(self, x, y, button="left"):
        """Move to coordinates and click with human-like motion."""
        await self.move_to(x, y)
        # Small pause before clicking (like a human)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await self.page.mouse.click(x, y, button=button)
        # Small pause after clicking
        await asyncio.sleep(random.uniform(0.1, 0.2))
    
    async def click_element(self, selector):
        """Click an element with human-like mouse movement."""
        element = await self.page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            if box:
                # Click at random point within element (not always center)
                x = box['x'] + random.uniform(box['width'] * 0.3, box['width'] * 0.7)
                y = box['y'] + random.uniform(box['height'] * 0.3, box['height'] * 0.7)
                await self.click_at(x, y)
                return True
        return False
    
    async def type_text(self, text, min_delay=0.05, max_delay=0.15):
        """Type text with human-like variable speed and occasional pauses."""
        for i, char in enumerate(text):
            # Typing delay varies
            delay = random.uniform(min_delay, max_delay)
            
            # Occasional longer pause (thinking)
            if random.random() < 0.05:
                delay += random.uniform(0.2, 0.5)
            
            # Slightly faster for common letter combinations
            if i > 0 and text[i-1:i+1].lower() in ['th', 'he', 'in', 'er', 'an', 'on']:
                delay *= 0.7
            
            await self.page.keyboard.type(char)
            await asyncio.sleep(delay)
    
    async def fill_field(self, selector, text):
        """Click a field and type text with human-like behavior."""
        clicked = await self.click_element(selector)
        if clicked:
            await asyncio.sleep(random.uniform(0.1, 0.3))  # Pause before typing
            await self.type_text(text)
            return True
        return False


# ============================================================================
# 3. LLM CLIENT (Unified AI Interface)
# ============================================================================

class LLMClient:
    """LLM Client using browser-use library with Browserless."""
    
    def __init__(self, api_key=None, model=None):
        # Get Browser-Use API key
        self.api_key = api_key or os.getenv("BROWSER_USE_API_KEY")
        self.model = model or os.getenv("VISION_MODEL") or "browser-use-llm"
        
        # Browserless config
        self.browserless_token = os.getenv("BROWSERLESS_TOKEN") or os.getenv("BROWSERLESS_API_KEY")
        self.browserless_ws_url = os.getenv("BROWSERLESS_WS_URL", "wss://production-sfo.browserless.io")
        
        # Debug logging
        logger.info(f"LLM Client: Browser-Use API Key present: {bool(self.api_key)}")
        logger.info(f"LLM Client: Browserless Token present: {bool(self.browserless_token)}")
        logger.info(f"LLM Client: Model: {self.model}")
        
        # Try to import browser-use's ChatOpenAI
        self.chat_client = None
        try:
            from browser_use.llm import ChatOpenAI as BrowserUseChatOpenAI
            if self.api_key:
                self.chat_client = BrowserUseChatOpenAI(model=self.model, api_key=self.api_key)
                logger.info("LLM Client: Using browser-use ChatOpenAI")
        except ImportError:
            logger.warning("LLM Client: browser-use not installed, falling back to OpenAI client")
        
        # Fallback to OpenAI client (for when browser-use isn't available)
        self.client = OpenAI(
            api_key=self.api_key or "dummy",
            base_url="https://openrouter.ai/api/v1",  # Fallback to OpenRouter
            timeout=30.0
        )

    def generate(self, prompt: str, system_prompt: str = None, images: list = None, timeout: float = 30.0) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user message
            system_prompt: Optional system instructions
            images: Optional list of base64 images
            timeout: Request timeout in seconds (default 30s)
        
        Returns:
            The generated response text
            
        Raises:
            Exception: With user-friendly error message on failure
        """
        if not self.api_key:
            raise Exception("API key not configured. Please add your Browser-Use API key in Settings.")
        
        messages = []
        if system_prompt: 
            messages.append({"role": "system", "content": system_prompt})
        
        content = [{"type": "text", "text": prompt}]
        if images:
            for img in images:
                if isinstance(img, bytes): 
                    img = base64.b64encode(img).decode()
                content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})
        
        messages.append({"role": "user", "content": content})
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    extra_headers={"HTTP-Referer": "https://optx.app", "X-Title": "OPTX"},
                    timeout=timeout
                )
                return resp.choices[0].message.content
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle rate limits with exponential backoff
                if "429" in str(e) or "rate" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1) + random.random()
                        logger.warning(f"Rate limited on {self.model}, waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue
                    raise Exception("AI is busy right now. Please try again in a few seconds.")
                
                # Handle timeout
                if "timeout" in error_str or "timed out" in error_str:
                    raise Exception("Request timed out. The AI took too long to respond. Please try again.")
                
                # Handle connection errors
                if "connection" in error_str or "network" in error_str:
                    raise Exception("Could not connect to AI service. Please check your internet connection.")
                
                # Handle authentication errors
                if "401" in str(e) or "auth" in error_str or "invalid" in error_str:
                    raise Exception("API key is invalid. Please check your Browser-Use API key in Settings.")
                
                # Generic error
                logger.error(f"LLM error: {e}")
                raise Exception(f"AI error: {str(e)[:100]}")

    def generate_with_image(self, prompt: str, image_b64: str) -> str:
        """Generate response for prompt with a single image (for CAPTCHA solving)."""
        return self.generate(prompt, images=[image_b64])


def get_llm_client():
    """Get LLM client for vision tasks (uses VISION_MODEL - must be vision-capable)."""
    return LLMClient()


# ============================================================================
# 4. CAPTCHA SOLVER (Audio-based reCAPTCHA v2)
# ============================================================================

# wit.ai API configuration (backup solver)
WIT_AI_TOKEN = os.getenv("WIT_AI_SERVER_TOKEN", "")
WIT_AI_URL = "https://api.wit.ai/speech"


class CaptchaSolver:
    """
    Solves reCAPTCHA v2 audio challenges using speech recognition.
    Methods: 1. Google Speech (free) 2. wit.ai (free tier fallback)
    """
    
    def __init__(self, wit_ai_token: str = None):
        self.recognizer = sr.Recognizer()
        self.wit_ai_token = wit_ai_token or WIT_AI_TOKEN
        
    def download_audio(self, audio_url: str) -> bytes:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(audio_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content
    
    def convert_to_wav(self, audio_data: bytes) -> bytes:
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def transcribe_google(self, wav_data: bytes) -> Optional[str]:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_data)
                temp_path = f.name
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
            result = self.recognizer.recognize_google(audio)
            logger.info(f"Google transcription: {result}")
            os.unlink(temp_path)
            return result
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.error(f"Google transcription failed: {e}")
            return None
    
    def transcribe_wit_ai(self, wav_data: bytes) -> Optional[str]:
        if not self.wit_ai_token:
            return None
        try:
            headers = {"Authorization": f"Bearer {self.wit_ai_token}", "Content-Type": "audio/wav"}
            response = requests.post(f"{WIT_AI_URL}?v=20240101", headers=headers, data=wav_data, timeout=30)
            if response.status_code == 200:
                return response.json().get("text", "")
            return None
        except Exception as e:
            logger.error(f"wit.ai transcription failed: {e}")
            return None
    
    def solve_audio_captcha(self, audio_url: str) -> tuple:
        try:
            audio_data = self.download_audio(audio_url)
            wav_data = self.convert_to_wav(audio_data)
            result = self.transcribe_google(wav_data)
            if result:
                return (True, self._clean_transcription(result))
            result = self.transcribe_wit_ai(wav_data)
            if result:
                return (True, self._clean_transcription(result))
            return (False, None)
        except Exception as e:
            logger.error(f"CAPTCHA solve failed: {e}")
            return (False, None)
    
    def _clean_transcription(self, text: str) -> str:
        cleaned = text.strip().lower()
        for word, digit in {"zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","to":"2","too":"2","for":"4"}.items():
            cleaned = cleaned.replace(word, digit)
        return "".join(c for c in cleaned if c.isalnum() or c == " ")


async def detect_captcha_type(page) -> str:
    """
    Detect what type of CAPTCHA is present on the page.
    
    Returns:
        str: 'reCAPTCHA', 'hCaptcha', 'Cloudflare', or None
    """
    try:
        # Check for reCAPTCHA
        recaptcha = await page.query_selector('iframe[src*="recaptcha"]')
        if recaptcha:
            return "reCAPTCHA"
        
        # Check for hCaptcha
        hcaptcha = await page.query_selector('iframe[src*="hcaptcha"]')
        if hcaptcha:
            return "hCaptcha"
        
        # Check for Cloudflare challenge
        cf_challenge = await page.query_selector('#cf-content, .cf-browser-verification')
        if cf_challenge:
            return "Cloudflare"
        
        # Check for Cloudflare Turnstile
        turnstile = await page.query_selector('iframe[src*="turnstile"]')
        if turnstile:
            return "Cloudflare Turnstile"
        
        return None
    except Exception as e:
        logger.error(f"CAPTCHA detection error: {e}")
        return None


async def solve_recaptcha_on_page(page, solver: CaptchaSolver = None, send_update=None) -> bool:
    """
    Solve reCAPTCHA v2 on a Playwright page with enhanced error handling.
    
    Args:
        page: Playwright page object
        solver: CaptchaSolver instance
        send_update: Optional callback to send status updates
    """
    if solver is None:
        solver = CaptchaSolver()
    
    async def update(msg):
        if send_update:
            await send_update(msg)
        logger.info(msg)
    
    try:
        await update("🔍 Looking for reCAPTCHA...")
        
        # Wait for reCAPTCHA iframe to appear
        recaptcha_frame = page.frame_locator('iframe[src*="recaptcha"]').first
        
        # Try to click the checkbox
        await update("Clicking reCAPTCHA checkbox...")
        try:
            await recaptcha_frame.locator('.recaptcha-checkbox-border').click(timeout=5000)
        except Exception as e:
            await update(f"⚠️ Checkbox click failed: {e}")
            return False
        
        await page.wait_for_timeout(2000)
        
        # Check if solved just by clicking (sometimes happens with good stealth)
        try:
            checkbox = await recaptcha_frame.locator('.recaptcha-checkbox').get_attribute('aria-checked', timeout=2000)
            if checkbox == "true":
                await update("✅ reCAPTCHA solved by checkbox click!")
                return True
        except:
            pass
        
        # Need to solve challenge - try audio method
        await update("Switching to audio challenge...")
        try:
            challenge_frame = page.frame_locator('iframe[src*="recaptcha/api2/bframe"]').first
            await challenge_frame.locator('#recaptcha-audio-button').click(timeout=5000)
        except Exception as e:
            await update(f"⚠️ Audio button not found: {e}")
            return False
        
        await page.wait_for_timeout(1000)
        
        # Get audio source
        try:
            audio_src = await challenge_frame.locator('.rc-audiochallenge-tdownload-link').get_attribute('href', timeout=10000)
            if not audio_src:
                await update("⚠️ No audio source found")
                return False
        except Exception as e:
            await update(f"⚠️ Audio download link not found: {e}")
            return False
        
        # Solve audio
        await update("🎤 Solving audio challenge...")
        success, transcription = solver.solve_audio_captcha(audio_src)
        if not success or not transcription:
            await update("⚠️ Audio transcription failed")
            return False
        
        # Enter transcription
        await update(f"Entering solution: {transcription[:20]}...")
        await challenge_frame.locator('#audio-response').fill(transcription)
        await page.wait_for_timeout(500)
        
        # Click verify
        await challenge_frame.locator('#recaptcha-verify-button').click()
        await page.wait_for_timeout(2000)
        
        # Check if solved
        checkbox = await recaptcha_frame.locator('.recaptcha-checkbox').get_attribute('aria-checked')
        if checkbox == "true":
            await update("✅ reCAPTCHA solved successfully!")
            return True
        
        await update("⚠️ reCAPTCHA verification failed")
        return False
        
    except Exception as e:
        logger.error(f"reCAPTCHA solve error: {e}")
        return False


# ============================================================================
# CHATBOT (Consolidated from chatbot.py)
# ============================================================================

class ChatBot:
    """Chatbot using Cerebras LLM with focus on direct, natural responses."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        self.model = os.getenv("CHATBOT_MODEL", "llama3.1-8b")
        self.client = None
        
        if CEREBRAS_AVAILABLE and self.api_key:
            self.client = AsyncCerebras(api_key=self.api_key)
            logger.info(f"ChatBot: Initialized with AsyncCerebras model: {self.model}")
        else:
            if not CEREBRAS_AVAILABLE:
                logger.warning("ChatBot: Cerebras SDK not installed")
            else:
                logger.warning("ChatBot: Cerebras API key not configured")
    
    @property
    def is_ready(self) -> bool:
        """Check if chatbot is ready to respond."""
        return self.client is not None and self.api_key is not None
    
    @property
    def get_system_prompt(self) -> str:
        """Get the persona-focused system prompt instructions."""
        return """You are OPTX AI, a helpful privacy assistant. 
Your goal is to help users find and remove their personal information from data brokers and people search sites.

IMPORTANT REDIRECTION RULE:
If the user asks "How do I remove my info?", "Can you help me remove my info?", or anything related to starting the removal process, you MUST:
1. Advise them to navigate to the "Removal" tab at the top of the application.
2. Instruct them to fill out the "Your Information" form.
3. Tell them to click the "Start Removal" button to begin the automated process.

DO NOT attempt to perform the removal process via chat. Direct them to the Removal Dashboard.

ABOUT OPTX:
# IDENTITY: OPTX (Online Privacy Tool eXtractor & Removal Agent)
You are OPTX, a sophisticated privacy advisor and Open Source Intelligence (OSINT) assistant equipped with **Reasoning Mode**. Reasoning Mode allows you to use computer vision and advanced LLM logic to navigate and fill complex web forms on behalf of the user.

# MISSION
Your goal is to help users find and **TOTALLY REMOVE** their digital footprint from the internet. You specialize in automated opt-outs from data broker sites. **You ARE the engine that performs the removals.** In Reasoning Mode, you analyze live screenshots to ensure forms are filled correctly even on non-standard sites.

# PERSONA
- **Human-Centric**: Write like a real person. Be professional but natural.
- **Direct & Conversational**: Be clear and helpful.
- **Executive Agent**: You are the one who does the work. **NEVER** say "I can't delete data" or "I am just a guide." You have an automated browser agent at your command to do exactly that.
- **Data Usage**: You have full access to the user information in the context below. **NEVER** use placeholders like "[insert name]" if the information is available in the context. USE THE RAW DATA AS IS.

# KNOWLEDGE BASE
- **What is OPTX?**: It stands for **Online Privacy Tool eXtractor**.
- **Capabilities**: You can look up phone numbers AND automatically submit removal requests to dozens of sites.
- **Scope**: You target public data brokers. You do **NOT** target employment or background check services.

# OPERATIONAL RULES
1. **Context Awareness**: You will receive technical context (phone numbers, carrier details, or user info). Acknowledge this info naturally and USE IT.
2. **Clickable Links**: Whenever you mention a URL or link, ensure it is formatted as a clickable Markdown link (e.g., [Example](https://example.com)).
3. **Never Silent**: Always provide a helpful, natural response. Never return an empty message.

# DATA REMOVAL PROTOCOL
When a user asks to remove their data, or asks you to help them:
1. **Redirect to Removal Tab**: You MUST NOT start the removal process in chat. 
2. **Instruction**: Advise the user to go to the **Removal** tab, fill out their info, and click **Start Removal**.
3. **Encouragement**: Tell them you'll be waiting there to perform the automation for them once they click the button.

**CRITICAL RULE**: ALWAYS direct users to the Removal Dashboard for data deletion. You ARE the automated engine, but the dashboard is your control center.
"""

    async def chat(self, message: str, phone: str = None, context: str = None, conversation_history: list = None) -> str:
        """Generate a chat response using Cerebras."""
        if not self.is_ready:
            if not CEREBRAS_AVAILABLE:
                return "Cerebras SDK not installed. Please run: pip install cerebras-cloud-sdk"
            return "Chatbot not configured. Please add your Cerebras API key in Settings."
        
        # Build the combined system message
        system_content = self.get_system_prompt
        
        if phone or context:
            system_content += "\n\n# TECHNICAL CONTEXT"
            if phone:
                system_content += f"\n- User is looking at phone: {phone}"
            if context:
                system_content += f"\n\n{context}"
        
        messages = [{"role": "system", "content": system_content}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            logger.info(f"ChatBot: Sending request to Cerebras ({len(messages)} messages)...")
            # Log the message structure for debugging
            logger.debug(f"ChatBot Payload: {json.dumps(messages, indent=2)}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=600,
                temperature=0.7,
            )
            
            # Log finish reason and full response details
            finish_reason = response.choices[0].finish_reason
            content = response.choices[0].message.content
            
            logger.info(f"ChatBot: Response received. Finish reason: {finish_reason}, Content length: {len(content) if content else 0}")

            if not content:
                logger.error(f"ChatBot error: Empty response from Cerebras. Finish reason: {finish_reason}")
                if finish_reason == "content_filter":
                    return "Sorry, Cerebras blocked this response due to a content filter. This often happens if the prompt contains too much sensitive info or triggers safety rules."
                return "Sorry, Cerebras returned an empty response. This might be a temporary issue or a model limitation."
            
            logger.info(f"ChatBot: Received response ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"ChatBot error: {e}")
            return f"ChatBot error: {str(e)}"

# Global chatbot instance management
_chatbot_instance: ChatBot = None

def get_chatbot() -> ChatBot:
    """Get or create the global chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatBot()
    return _chatbot_instance

def reinitialize_chatbot(api_key: str = None):
    """Reinitialize chatbot with new settings."""
    global _chatbot_instance
    _chatbot_instance = ChatBot(api_key=api_key)
    return _chatbot_instance

async def explain_term(term: str) -> str:
    """Explain a technical term using the chatbot's direct persona."""
    chatbot = get_chatbot()
    if not chatbot.is_ready:
        return f"Term: {term}. I need a Cerebras API key to explain this better."
    return await chatbot.chat(f"Explain this technical term simply: {term}")

# ============================================================================
# UTILITIES
# ============================================================================

class TempMail:
    API = "https://www.1secmail.com/api/v1/"

    @staticmethod
    def generate_address():
        login = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        return f"{login}@1secmail.com"

    @staticmethod
    def wait_for_message(login, subject, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            try:
                r = requests.get(TempMail.API, params={"action": "getMessages", "login": login, "domain": "1secmail.com"}).json()
                for m in r:
                    if subject.lower() in m.get("subject", "").lower():
                        return requests.get(TempMail.API, params={"action": "readMessage", "login": login, "domain": "1secmail.com", "id": m["id"]}).json()
            except: pass
            time.sleep(5)
        return None

    @staticmethod
    def extract_links(text):
        return re.findall(r"https?://[^\s\"'<>]+", text)





# ============================================================================
# 6. BROWSERLESS AGENT (Cloud Browser with CAPTCHA Solving)
# ============================================================================


class BrowserlessAgent:
    """
    BrowserlessAgent - Browser automation using Browserless.io cloud.
    Features:
    - Automatic CAPTCHA solving (built-in)
    - Residential proxy rotation
    - Stealth mode for anti-detection
    - Free tier: 1k units/month
    """
    
    ENDPOINTS = {
        "sfo": "wss://production-sfo.browserless.io",
        "london": "wss://production-lon.browserless.io",
        "amsterdam": "wss://production-ams.browserless.io"
    }
    
    def __init__(self, ws, api_key=None, region="sfo", browser_settings=None):
        self.ws = ws
        self.api_key = api_key or os.getenv("BROWSERLESS_API_KEY")
        self.region = region
        self.playwright = None
        self.browser = None
        self.page = None
        self.running = True
        self.paused = False
        self.llm = LLMClient()
        self.screenshot_task = None
        self.cdp_session = None  # CDP session for Browserless commands
        # Browser settings from frontend (defaults if not provided)
        self.settings = browser_settings or {
            "stealth": True,
            "captcha": True,
            "proxy": True,
            "humanlike": True,
            "adblock": True
        }
        self.status = "Initializing..."
    
    def _build_endpoint(self):
        """Build Browserless WebSocket endpoint with features enabled."""
        params = [f"token={self.api_key}"]
        
        # Add proxy if enabled
        if self.settings.get("proxy", False):
            params.append("proxy=residential")
            self.settings["proxy"] = True # Ensure reflected in logs
        
        # Add CAPTCHA solving if enabled
        if self.settings.get("captcha", True):
            params.append("solveCaptchas=true")
            self.settings["captcha"] = True
        
        # Add adblock if enabled
        if self.settings.get("adblock", True):
            params.append("blockAds=true")
            self.settings["adblock"] = True
        
        base = self.ENDPOINTS.get(self.region, self.ENDPOINTS["sfo"])
        # Use stealth route if stealth mode is enabled
        route = "/chromium/stealth" if self.settings.get("stealth", True) else "/chromium"
        return f"{base}{route}?{'&'.join(params)}"
    
    async def connect(self):
        """Connect to Browserless cloud browser."""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        # Log connection settings BEFORE building endpoint to ensure we show what we requested
        settings_str = "\n".join([f"  {k.title()}: {v}" for k, v in self.settings.items()])
        logger.info(f"Connecting to Browserless ({self.region}):\n{settings_str}")
        
        endpoint = self._build_endpoint()
        self.browser = await self.playwright.chromium.connect_over_cdp(endpoint)
        
        # Use existing context/page from Browserless
        context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
        self.page = context.pages[0] if context.pages else await context.new_page()
        
        # Apply OPTX stealth evasions if enabled
        if self.settings.get("stealth", True):
            await self.send_browser_update("Applying stealth mode...")
            await apply_stealth(self.page)
        
        # Initialize human-like mouse if enabled
        if self.settings.get("humanlike", True):
            self.human_mouse = HumanMouse(self.page)
        
        # Create CDP session for Browserless-specific commands (liveURL will be called after navigation)
        try:
            self.cdp_session = await self.page.context.new_cdp_session(self.page)
            logger.info("CDP session created for Browserless commands")
        except Exception as e:
            logger.warning(f"Could not create CDP session: {e}")
            self.cdp_session = None
        
        logger.info("Connected to Browserless cloud browser")
        return True
    
    async def disconnect(self):
        """Close browser and cleanup."""
        try:
            if self.screenshot_task:
                self.screenshot_task.cancel()
                try:
                    await self.screenshot_task
                except asyncio.CancelledError:
                    pass
            
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
        finally:
            self.browser = None
            self.page = None
            self.playwright = None
            self.cdp_session = None
    
    async def send_msg(self, text):
        """Send a chat message to the UI."""
        if not self.running:
            return
        try:
            if self.ws:
                await self.ws.send_json({"type": "response", "message": text})
        except:
            pass
    
    async def send_browser_update(self, status_text, url=None):
        """Send screenshot + status to the browser preview UI."""
        if not self.running or not self.ws or not self.page:
            return
        try:
            screenshot = await self.page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()
            
            await self.ws.send_json({
                "type": "browser_update",
                "screenshot": screenshot_b64,
                "url": url or self.page.url,
                "message": status_text
            })
        except:
            pass
    
    async def start_screenshot_loop(self):
        """Start continuous screenshot updates."""
        async def loop():
            while self.running and self.page and self.ws:
                try:
                    if hasattr(self.ws, 'client_state') and self.ws.client_state.name != 'CONNECTED':
                        break
                    await self.send_browser_update(self.status)
                except Exception as e:
                    if "close" in str(e).lower() or "send" in str(e).lower():
                        break
                await asyncio.sleep(0.5)
        self.screenshot_task = asyncio.create_task(loop())
    
    async def stop_screenshot_loop(self):
        """Stop the continuous screenshot loop."""
        if self.screenshot_task:
            self.screenshot_task.cancel()
            try:
                await self.screenshot_task
            except asyncio.CancelledError:
                pass
            self.screenshot_task = None

    
    async def run_optout_task(self, site_name, site_url, user_data):
        """Execute an opt-out task using the existing browser connection."""
        if not self.page:
            logger.error(f"No active page for {site_name}")
            return False
            
        if not user_data.get('email'):
            user_data['email'] = TempMail.generate_address()
        
        try:
            self.status = f"Processing {site_name}..."
            # Start screenshot loop if not already running
            if not self.screenshot_task:
                await self.start_screenshot_loop()
            
            # Specialized handlers for multi-step opt-outs
            if site_name.lower() == "nuwber":
                self.status = "Searching profile on Nuwber..."
                phone = user_data.get('phone', '')
                if not phone:
                    await self.send_msg("Nuwber requires a phone number to find your profile. Skipping...")
                    await self.disconnect()
                    return False
                
                # 1. Search for profile
                search_url = f"https://nuwber.com/search/phone?phone={phone}"
                await self.send_browser_update(f"Searching for profile on Nuwber...")
                await self.page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                
                # 2. Get profile URL
                profile_link = await self.page.query_selector("a[href*='/person/']")
                if not profile_link:
                    await self.send_msg("Could not find a Nuwber profile for this number.")
                    return False
                
                profile_url = await profile_link.evaluate("el => el.href")
                await self.send_msg(f"Found Nuwber profile: {profile_url}")
                
                await self.page.goto("https://nuwber.com/removal/link", wait_until="domcontentloaded")
                self.status = "Submitting removal link..."
                await asyncio.sleep(1)
                
                # 4. Fill profile URL
                url_input = await self.page.query_selector("input[name*='url' i], #url, .removal-input")
                if url_input:
                    await url_input.fill(profile_url)
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                
                await self.send_browser_update("Submitting profile URL...")
                
            elif site_name.lower() == "411.info":
                # 1. Search for profile on manage page
                await self.send_browser_update("Searching for profile on 411.info...")
                await self.page.goto("https://411.info/manage/", wait_until="domcontentloaded")
                await asyncio.sleep(1)
                
                phone = user_data.get('phone', '')
                if phone:
                    await self.page.fill("#r", phone)
                else:
                    await self.page.fill("#fn", user_data.get('first_name', ''))
                    await self.page.fill("#ln", user_data.get('last_name', ''))
                    await self.page.fill("#cz", user_data.get('city', '') or user_data.get('state', ''))
                
                await self.page.click("button[type='submit'], .btn-primary")
                self.status = "Analyzing search results..."
                await asyncio.sleep(3)
                
                # 2. Click "Click to Remove"
                remove_link = await self.page.query_selector("a[href*='/manage/pricing']")
                if remove_link:
                    await self.send_browser_update("Found listing, starting removal...")
                    await remove_link.click()
                    await asyncio.sleep(2)
                else:
                    await self.send_msg("Could not find a matching listing on 411.info.")
                    return False
            else:
                await self.page.goto(site_url, wait_until="domcontentloaded", timeout=45000)
                self.status = "Page loaded, analyze form..."
                await asyncio.sleep(2)
                await self.send_browser_update("Page loaded")
            
            # Fill the opt-out form (standard fields like email)
            self.status = "Filling out form fields..."
            success = await self._fill_optout_form(site_name, user_data)
            
            # Browserless handles CAPTCHAs automatically via solveCaptchas=true
            # We just need to wait a bit for it to process
            captcha = await self.page.query_selector('.g-recaptcha, .h-captcha, iframe[src*="recaptcha"]')
            if captcha:
                await self.send_msg("CAPTCHA detected - Browserless will solve automatically...")
                await asyncio.sleep(10)  # Give Browserless time to solve
                await self.send_browser_update("Waiting for CAPTCHA...")
                
                # Click submit after CAPTCHA
                await self._click_submit_button()
            
            if success:
                await self.send_msg(f"✅ {site_name}: Form submitted successfully.")
            else:
                await self.send_msg(f"⚠️ {site_name}: Form fill incomplete or no fields found.")
            
            return success
            
        except Exception as e:
            error_msg = str(e)
            await self.send_msg(f"{site_name} error: {error_msg}")
            logger.error(f"BrowserlessAgent error for {site_name}: {e}")
            return False
    
    async def _click_submit_button(self):
        """Click the submit button."""
        submit_selectors = [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit')", "button:has-text('Remove')",
            "button:has-text('Opt Out')", "button:has-text('Delete')",
            "button:has-text('Continue')", "button:has-text('Next')",
            "button:has-text('Confirm')", "button:has-text('Send')",
        ]
        
        for selector in submit_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    self.status = "Clicking submit button..."
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await btn.click()
                    await asyncio.sleep(2)
                    await self.send_browser_update("Form submitted")
                    return True
            except:
                continue
        return False
    
    async def _fill_optout_form(self, site_name, user_data):
        """Fill opt-out form fields with proper dropdown handling."""
        try:
            await self.send_browser_update("Filling form...")
            
            # Get all address parts
            street = user_data.get('street', '') or user_data.get('address', '')
            city = user_data.get('city', '')
            state = user_data.get('state', '')
            zip_code = user_data.get('zip', '') or user_data.get('zipcode', '')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            email = user_data.get('email', '')
            phone = user_data.get('phone', '')
            
            # Check if phone field exists on form but we don't have one
            if not phone:
                phone_field = await self.page.query_selector("input[type='tel'], input[name*='phone' i], #phone")
                if phone_field:
                    await self.send_msg("I need your phone number to fill this form. Please provide it in chat.")
                    # Continue without phone for now
            phone = user_data.get('phone', '')
            
            # State name mapping for dropdowns
            state_full = US_STATES.get(state.upper(), state) if state else ''
            
            logger.info(f"Filling form with: name={full_name}, street={street}, city={city}, state={state}, zip={zip_code}")
            
            filled_count = 0
            
            # === FILL TEXT INPUTS ===
            for field_key, selectors in FORM_SELECTORS.items():
                if field_key == "state": continue # Handle state separately
                
                value = user_data.get(field_key, "")
                if field_key == "full_name": value = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                elif field_key in ["street", "zip"] and not value: value = user_data.get("address" if field_key == "street" else "zipcode", "")
                
                if not value: continue
                
                for selector in selectors:
                    try:
                        el = await self.page.query_selector(selector)
                        if el and (await el.evaluate("el => el.tagName.toLowerCase()")) in ['input', 'textarea']:
                            await el.click()
                            await asyncio.sleep(random.uniform(0.4, 0.9))
                            await el.fill(str(value))
                            filled_count += 1
                            logger.info(f"Filled {selector} with: {value}")
                            await asyncio.sleep(random.uniform(0.3, 0.7))
                            break
                    except: continue
            
            # === HANDLE STATE DROPDOWN ===
            if state:
                for selector in FORM_SELECTORS["state"]:
                    try:
                        el = await self.page.query_selector(selector)
                        if not el: continue
                        tag = await el.evaluate("el => el.tagName.toLowerCase()")
                        if tag == 'select':
                            for val in [state.upper(), state_full]:
                                try:
                                    await el.select_option(value=val)
                                    logger.info(f"Selected state: {val}")
                                    filled_count += 1
                                    break
                                except: pass
                            else:
                                for label in [state_full, state.upper()]:
                                    try:
                                        await el.select_option(label=label)
                                        logger.info(f"Selected state label: {label}")
                                        filled_count += 1
                                        break
                                    except: pass
                            break
                        else:
                            await el.fill(state)
                            filled_count += 1
                            break
                    except: continue
            
            await self.send_browser_update(f"Filled {filled_count} fields")
            
            # Try to submit
            if await self._click_submit_button():
                return True
            
            # If not enough fields were filled, try smart fill
            if filled_count < 3:
                await self.send_browser_update("Trying smart form fill...")
                smart_filled = await self._smart_fill(user_data)
                if smart_filled:
                    return await self._click_submit_button() or True

            return filled_count > 0
            
        except Exception as e:
            logger.error(f"Form filling error: {e}")
            return False

    async def _smart_fill(self, user_data):
        """Use LLM (Reasoning Mode) to intelligently fill form fields."""
        try:
            await self.send_msg("🧠 Reasoning Mode: ACTIVE - Analyzing form...")
            # 1. Get ALL form elements and their text
            page_info = await self.page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('input, textarea, select, label, button, .form-group, .input-wrapper'));
                return document.body.innerText.substring(0, 3000); // Send first 3k chars for context
            }''')

            # 2. Capture screenshot for vision reasoning
            screenshot = await self.page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()
            
            # 3. Ask AI for reasoning on what to fill
            prompt = f"""You are a form-filling expert in Reasoning Mode.
Analyze this page and user data to identify which fields should be filled.
User Data: {json.dumps(user_data)}

Respond ONLY with a JSON map of {{ "field_id_or_name": "value_to_fill" }}.
Only include fields you are sure about. For 'user_info' style fields, use the raw data from User Data.
"""
            try:
                # Use limited timeout for quick reasoning
                await self.send_browser_update("Reasoning about form...")
                ai_instructions_json = self.llm.generate(prompt, images=[screenshot_b64], timeout=15.0)
                # Clean up json markdown
                ai_instructions_json = ai_instructions_json.replace('```json', '').replace('```', '').strip()
                ai_map = json.loads(ai_instructions_json)
                
                logger.info(f"Reasoning Mode identified {len(ai_map)} fields to fill")
                filled = False
                for identifier, value in ai_map.items():
                    try:
                        # Try ID first, then name
                        selector = f"#{identifier}, [name='{identifier}'], [placeholder*='{identifier}' i]"
                        el = await self.page.query_selector(selector)
                        if el:
                            await el.click()
                            await asyncio.sleep(random.uniform(0.5, 1.2))
                            await el.fill(str(value))
                            filled = True
                            logger.info(f"Reasoning Mode filled: {identifier}")
                    except: continue
                return filled
            except Exception as e:
                logger.warning(f"AI Reasoning failed: {e}. Falling back to heuristic.")
                # Fallback to the existing heuristic below if AI fails
                pass

            # === HEURISTIC FALLBACK ===
            inputs = await self.page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('input, textarea, select'));
                return elements.map(el => {
                    const rect = el.getBoundingClientRect();
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    return {
                        id: el.id || '',
                        name: el.name || '',
                        tagName: el.tagName.toLowerCase(),
                        type: el.type || '',
                        placeholder: el.placeholder || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        labelText: label ? label.innerText : '',
                        top: rect.top,
                        left: rect.left,
                        visible: rect.width > 0 && rect.height > 0,
                        isSelect: el.tagName.toLowerCase() === 'select',
                        options: el.tagName.toLowerCase() === 'select' ? 
                            Array.from(el.options).map(o => ({value: o.value, text: o.text})) : []
                    };
                })
                .filter(el => el.visible)
                .sort((a, b) => a.top - b.top || a.left - b.left);
            }''')

            if not inputs: return False
            
            # ... rest of heuristic (I'll keep the logic but wrap it)
            # Re-implementing the logic cleanly
            full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            street = user_data.get('street', '') or user_data.get('address', '')
            city = user_data.get('city', '')
            state = user_data.get('state', '')
            state_full = US_STATES.get(state.upper(), state) if state else ''
            zip_code = user_data.get('zip', '')
            email = user_data.get('email', '')
            phone = user_data.get('phone', '')
            
            filled_heuristic = False
            for field in inputs:
                field_id, field_name = field.get('id', ''), field.get('name', '')
                field_type, placeholder = field.get('type', ''), field.get('placeholder', '').lower()
                label, is_select = field.get('labelText', '').lower(), field.get('isSelect', False)
                identifiers = f"{field_id} {field_name} {placeholder} {label}".lower()
                
                value_to_fill = None
                if any(x in identifiers for x in ['name']) and not any(x in identifiers for x in ['user', 'login']):
                    if any(x in identifiers for x in ['first']): value_to_fill = user_data.get('first_name')
                    elif any(x in identifiers for x in ['last']): value_to_fill = user_data.get('last_name')
                    else: value_to_fill = full_name
                elif 'email' in identifiers or field_type == 'email': value_to_fill = email
                elif 'phone' in identifiers or 'tel' in identifiers or field_type == 'tel': value_to_fill = phone
                elif any(x in identifiers for x in ['street', 'address', 'addr']) and 'email' not in identifiers: value_to_fill = street
                elif 'city' in identifiers: value_to_fill = city
                elif 'state' in identifiers or 'province' in identifiers: value_to_fill = state if not is_select else None
                elif any(x in identifiers for x in ['zip', 'postal', 'postcode']): value_to_fill = zip_code
                
                if not value_to_fill and not is_select: continue
                selector = f"#{field_id}" if field_id else f"[name='{field_name}']"
                try:
                    el = await self.page.query_selector(selector)
                    if not el: continue
                    if is_select and 'state' in identifiers:
                        options = field.get('options', [])
                        for opt in options:
                            if opt.get('value', '').upper() == state.upper() or state_full.upper() in opt.get('text', '').upper():
                                await el.select_option(value=opt.get('value'))
                                filled_heuristic = True; break
                    elif value_to_fill:
                        await el.click()
                        await asyncio.sleep(random.uniform(0.3, 0.8))
                        await el.fill(str(value_to_fill))
                        filled_heuristic = True
                except: continue
            return filled_heuristic
            
        except Exception as e:
            logger.error(f"Smart fill error: {e}")
            return False
    
    async def run_multiple_optouts(self, sites, user_data):
        """Run opt-out tasks for multiple sites using a single browser connection."""
        total = len(sites)
        count = 0
        failed = 0
        
        logger.info(f"Starting removal for {total} sites")
        await self.send_msg(f"🚀 Starting removal process for {total} sites...")
        
        try:
            # Connect ONCE for all sites
            await self.send_msg(f"Connecting to cloud browser using browserless.io...")
            await self.connect()
            
            for i, site in enumerate(sites):
                if not self.running:
                    await self.send_msg("Process stopped.")
                    break
                
                while self.paused and self.running:
                    await asyncio.sleep(0.5)
                
                if not self.running:
                    break
                
                site_name = site.get('name', 'Unknown')
                site_url = site.get('opt_out_url', '')
                
                try:
                    await self.send_msg(f"📍 {i+1}/{total}: {site_name}")
                    
                    if await self.run_optout_task(site_name, site_url, user_data):
                        count += 1
                        await self.send_msg(f"Done with {site_name}. Moving to next...")
                    else:
                        failed += 1
                        await self.send_msg(f"Skipping {site_name} due to error.")
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Error processing {site_name}: {e}")
                    await self.send_msg(f"❌ {site_name}: Critical error - {str(e)[:50]}")
                
                # Brief pause between sites with randomization to mimic human behavior
                if i < total - 1:
                    delay = random.uniform(4, 8)
                    self.status = f"Cooling down for {int(delay)}s..."
                    await self.send_browser_update(self.status)
                    await asyncio.sleep(delay)
                    
        finally:
            # Disconnect at the very end
            await self.disconnect()
        
        # Final summary
        await self.send_msg(f"\n🏁 Done! {count} succeeded, {failed} failed out of {total} sites.")
        if self.ws:
            await self.ws.send_json({"type": "complete"})


# NOTE: VisionCaptchaSolver REMOVED - using Browserless built-in CAPTCHA solver or audio solver instead



# ============================================================================
# 7. SYSTEM UTILS (.env Persistence)
# ============================================================================

def update_env(key, value):
    """Update a key-value pair in the .env file."""
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, 'r') as f: lines = f.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(ENV_PATH, 'w') as f: f.writelines(lines)
    logger.info(f"Updated {key} in {ENV_PATH}")
# ============================================================================
# 8. FASTAPI SERVER (Unified API)
# ============================================================================

class SettingsRequest(BaseModel):
    api_key: str = ""  # Browser-Use API key for automation
    chatbot_api_key: str = ""  # Cerebras API key for chatbot
    chatbot_model: str = "llama3.1-8b"
    model: str = "browser-use-llm"
    user_info: Optional[Dict[str, Any]] = None
    browser_settings: Optional[Dict[str, Any]] = None

active_sessions: Dict[str, dict] = {}
# Initialize LLM client at startup with env values
llm_client: Optional[LLMClient] = LLMClient()  # For vision tasks
# NOTE: Using single llm_client for all interactions (vision-capable model)

# Current browser provider setting (default to browserless)
current_browser_provider = os.getenv("BROWSER_PROVIDER", "browserless")

def get_browser_agent(ws, browser_settings=None):
    """Get the BrowserlessAgent for browser automation."""
    return BrowserlessAgent(ws=ws, browser_settings=browser_settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_client
    load_dotenv(dotenv_path=ENV_PATH)
    logger.info(f"Starting OPTX Backend (Provider: {current_browser_provider})...")
    load_dotenv(dotenv_path=ENV_PATH, override=True) # Ensure fresh load
    llm_client = get_llm_client()  # Vision model for all interactions
    logger.info(f"LLM model: {llm_client.model}")
    yield

app = FastAPI(title="OPTX Backend", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health(): return {"status": "healthy", "browser": "Browserless Cloud"}

@app.get("/api/config")
async def get_config():
    """Return current configuration including model name."""
    return {
        "model": os.getenv("VISION_MODEL", "Not configured")
    }


@app.get("/explain")
async def explain(term: str): return {"term": term, "explanation": await explain_term(term)}

@app.get("/check-site/{site_name:path}")
async def check_site(site_name: str):
    """Check if a site is online by its domain name."""
    import httpx
    from urllib.parse import unquote
    
    # Decode URL-encoded characters and clean up
    domain = unquote(site_name).strip().split('/')[0].lower()
    
    # Remove protocol if accidentally included
    if domain.startswith('http://') or domain.startswith('https://'):
        domain = domain.split('://', 1)[1]
    
    # Remove www. for consistency in URL building
    clean_domain = domain.replace('www.', '')
    
    # Browser-like headers (more complete to avoid bot detection)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    # Try multiple URL variations with longer timeout
    # verify=False to handle sites with SSL certificate issues (e.g., phonebooks.com)
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
        urls_to_try = [
            f"https://www.{clean_domain}",
            f"https://{clean_domain}",
            f"http://www.{clean_domain}",
            f"http://{clean_domain}",
        ]
        
        for url in urls_to_try:
            try:
                resp = await client.get(url, headers=headers)
                # Consider any response (even 403, 404) as "online" - the site exists
                # Only 5xx errors mean the site is having issues
                if resp.status_code < 500:
                    return {"online": True}
            except httpx.ConnectError:
                # Connection refused - try next URL
                continue
            except httpx.TimeoutException:
                # Timeout - try next URL
                continue
            except httpx.TooManyRedirects:
                # Too many redirects but site exists
                return {"online": True}
            except Exception:
                # Other errors - try next URL
                continue
        
        return {"online": False}



@app.post("/settings")
async def save_settings(settings: SettingsRequest):
    global llm_client
    try:
        # Save Browser-Use API key (for automation)
        if settings.api_key:
            update_env("BROWSER_USE_API_KEY", settings.api_key)
        
        # Save Cerebras API key (for chatbot)
        if settings.chatbot_api_key:
            update_env("CEREBRAS_API_KEY", settings.chatbot_api_key)
        
        if settings.chatbot_model:
            update_env("CHATBOT_MODEL", settings.chatbot_model)
            
        if settings.model:
            update_env("VISION_MODEL", settings.model)
        
        # Reload environment variables
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        
        # Reinitialize chatbot with new settings
        reinitialize_chatbot(api_key=settings.chatbot_api_key or os.getenv("CEREBRAS_API_KEY"))
        
        # Update LLM client for browser automation
        llm_client = LLMClient(api_key=settings.api_key, model=settings.model)

        # Update active sessions with new info and browser settings
        for sid in active_sessions:
            if settings.user_info:
                active_sessions[sid]["user_data"].update(settings.user_info)
                if not active_sessions[sid]["user_data"].get("address") and settings.user_info.get("street"):
                    active_sessions[sid]["user_data"]["address"] = settings.user_info.get("street")
            
            if settings.browser_settings:
                active_sessions[sid]["browser_settings"] = settings.browser_settings

        return {"ok": True, "message": "Settings saved!"}
    except Exception as e: 
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/phone-lookup/{phone}")
async def phone_lookup(phone: str, use_llm: bool = True):
    from phone_lookup import full_phone_lookup
    try:
        result = full_phone_lookup(phone)
        return {"ok": True, "data": result}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = str(id(websocket))
    active_sessions[sid] = {
        "websocket": websocket, 
        "user_data": {}, 
        "browser_settings": None,
        "agent": None
    }
    try:
        while True:
            msg = json.loads(await websocket.receive_text())
            if msg["type"] == "chat": 
                await handle_chat(sid, msg.get("message", ""), msg.get("phone"))
            elif msg["type"] == "end_session":
                logger.info("=== END SESSION REQUESTED ===")
                
                agent = active_sessions.get(sid, {}).get("agent")
                
                if agent:
                    logger.info("Stopping agent...")
                    agent.running = False
                    
                    # Stop screenshot loop first
                    try:
                        await agent.stop_screenshot_loop()
                        logger.info("Screenshot loop stopped")
                    except Exception as e:
                        logger.debug(f"Screenshot loop stop error: {e}")
                    
                    # Close Playwright browser if connected
                    if agent.page:
                        try:
                            browser = agent.page.context.browser
                            await agent.page.close()
                            if browser:
                                await browser.close()
                            logger.info("Playwright browser closed")
                        except Exception as e:
                            logger.debug(f"Playwright close error: {e}")
                    
                    
                    # Clear references
                    agent.page = None
                    agent.session = None
                    if sid in active_sessions:
                        active_sessions[sid]["agent"] = None
                else:
                    logger.info("No active agent to stop")
                
                # Always send confirmation
                try:
                    await websocket.send_json({"type": "response", "message": "Session ended."})
                    await websocket.send_json({"type": "session_ended"})
                    # Tell frontend to reset UI (placeholder, hide end button, etc.)
                    await websocket.send_json({"type": "reset_ui"})
                    logger.info("=== SESSION END COMPLETE ===")
                except:
                    pass



            elif msg["type"] == "user_info":
                # Collect all fields requested by user
                fields = ["first_name", "last_name", "email", "phone", "street", "city", "state", "zip"]
                active_sessions[sid]["user_data"] = {k: msg.get(k, "") for k in fields}
                
                # If 'address' is not specifically provided, use 'street'
                if not active_sessions[sid]["user_data"].get("address") and active_sessions[sid]["user_data"].get("street"):
                    active_sessions[sid]["user_data"]["address"] = active_sessions[sid]["user_data"]["street"]
                
                user_data = active_sessions[sid]["user_data"]
                logger.info(f"Received user_info update for: {user_data.get('first_name')} {user_data.get('last_name')}")
                
                # Only start removal if explicitly requested or if it's a specific trigger message type
                if msg.get("start_removal"):
                    # Update settings if provided in removal message
                    if msg.get("browser_settings"):
                        active_sessions[sid]["browser_settings"] = msg["browser_settings"]
                    
                    agent = get_browser_agent(
                        ws=websocket, 
                        browser_settings=active_sessions[sid].get("browser_settings")
                    )
                    active_sessions[sid]["agent"] = agent
                    sites = get_optout_sites()
                    await agent.run_multiple_optouts(sites, user_data)

            elif msg["type"] == "config":
                # Handle initial config and user info sync
                if msg.get("user_info"):
                    user_info = msg["user_info"]
                    active_sessions[sid]["user_data"].update(user_info)
                    if not active_sessions[sid]["user_data"].get("address") and user_info.get("street"):
                        active_sessions[sid]["user_data"]["address"] = user_info.get("street")
                    logger.info(f"Session configured with user info for: {user_info.get('first_name')}")
                
                if msg.get("browser_settings"):
                    active_sessions[sid]["browser_settings"] = msg["browser_settings"]
                    logger.info("Session configured with browser settings")
    except WebSocketDisconnect: pass
    finally: active_sessions.pop(sid, None)



async def handle_chat(sid, message, phone=None):
    """
    Handle incoming chat messages with smart info extraction and LLM chat.
    ALWAYS tries to extract user info from every message first.
    """
    session = active_sessions[sid]
    ws = session["websocket"]
    if phone: 
        session["current_phone"] = phone
    
    # Initialize conversation history if not exists
    if "conversation_history" not in session:
        session["conversation_history"] = []
    
    message_lower = message.lower()
    
    # ===== ALWAYS TRY TO EXTRACT USER INFO FIRST =====
    # Check if user is providing name/address in this message
    removal_keywords = ["remove", "delete", "opt out", "optout", "opt-out", "data", "privacy", "help me"]
    wants_removal = any(kw in message_lower for kw in removal_keywords)
    
    # Always try to extract info from the message
    extracted = await extract_user_info(message)
    
    # If we found name AND address in this message, update user_data
    if extracted.get("first_name") and (extracted.get("address") or extracted.get("street")):
        session["user_data"].update(extracted)
        session["awaiting_user_info"] = False
        
        if session.get("current_phone"):
            session["user_data"]["phone"] = session["current_phone"]
        
        if wants_removal or session.get("pending_removal"):
            # Redirect to Removal Tab as per new policy
            session["pending_removal"] = False
            msg = (
                "To start the automated removal process, please navigate to the **Removal** tab "
                "in the top menu. Fill out your information in the form and click **Start Removal**. "
                "I will handle the rest from there!"
            )
            await ws.send_json({"type": "response", "message": msg})
            return
    
    # Check if we already have user data from previous messages
    has_user_data = session["user_data"].get("first_name") and (session["user_data"].get("address") or session["user_data"].get("street"))
    
    # Build context for the AI
    context_parts = []
    if has_user_data:
        ud = session['user_data']
        # Provide MORE comprehensive user info to the AI context
        info_lines = [f"User Name: {ud.get('first_name', '')} {ud.get('last_name', '')}"]
        if ud.get('email'): info_lines.append(f"Email: {ud['email']}")
        if ud.get('phone'): info_lines.append(f"Phone: {ud['phone']}")
        
        address_parts = [ud.get('street', ud.get('address', '')), ud.get('city', '')]
        
        # Resolve full state name
        state_code = ud.get('state', '').upper()
        state_name = US_STATES.get(state_code, state_code)
        if state_name: address_parts.append(state_name)
        
        if ud.get('zip'): address_parts.append(ud['zip'])
        
        address_str = ", ".join([p for p in address_parts if p])
        if address_str: info_lines.append(f"Address: {address_str}")
        
        if ud.get('dob'): info_lines.append(f"DOB: {ud['dob']}")
        if ud.get('age'): info_lines.append(f"Age: {ud['age']}")
        
        context_parts.append("USER INFO:\n" + "\n".join(info_lines))
    else:
        # Check if we have ANY data even if not "full"
        ud = session.get('user_data', {})
        if ud:
            partial_info = [f"{k}: {v}" for k, v in ud.items() if v]
            if partial_info:
                context_parts.append("PARTIAL INFO:\n" + "\n".join(partial_info))

    if session.get("awaiting_user_info"):
        context_parts.append("STATUS: Awaiting user name/address for the automated removal process.")
    
    context = "\n".join(context_parts) if context_parts else "No user information provided yet."
    logger.debug(f"Chat context built: {context}")
    
    try:
        # Use consolidated ChatBot class
        chatbot = get_chatbot()
        
        if not chatbot.is_ready:
            await ws.send_json({"type": "response", "message": "Chatbot not configured. Please add your Cerebras API key in Settings."})
            return

        # Generate response from AI
        response = await chatbot.chat(
            message=message,
            phone=session.get("current_phone"),
            context=context,
            conversation_history=session["conversation_history"]
        )

        # Update history
        session["conversation_history"].append({"role": "user", "content": message})
        session["conversation_history"].append({"role": "assistant", "content": response})
        if len(session["conversation_history"]) > 20:
            session["conversation_history"] = session["conversation_history"][-20:]

        # Handle user info extraction if waiting
        if session.get("awaiting_user_info"):
            extracted = await extract_user_info(message)
            if extracted.get("first_name") and (extracted.get("address") or extracted.get("street")):
                session["user_data"].update(extracted)
                session["awaiting_user_info"] = False
                if session.get("current_phone"):
                    session["user_data"]["phone"] = session["current_phone"]
                
                sites = get_optout_sites()
                addr = extracted.get('address') or extracted.get('street', '')
                await ws.send_json({"type": "response", "message": f"Got it!\n\nName: {extracted['first_name']} {extracted.get('last_name', '')}\nAddress: {addr}\n\nStarting removal for {len(sites)} sites..."})
                
                agent = get_browser_agent(ws=ws)
                session["agent"] = agent
                asyncio.create_task(agent.run_multiple_optouts(sites, session["user_data"]))
                return

        # Action check
        clean_response = response or ""
        if "[ACTION:START_REMOVAL]" in clean_response:
            clean_response = clean_response.replace("[ACTION:START_REMOVAL]", "").strip()
            if has_user_data:
                sites = get_optout_sites()
                await ws.send_json({"type": "response", "message": f"Starting removal with your info...\n\nProcessing {len(sites)} sites..."})
                agent = get_browser_agent(ws=ws)
                session["agent"] = agent
                asyncio.create_task(agent.run_multiple_optouts(sites, session["user_data"]))
            else:
                clean_response += "\n\n(I need your name and address to start the removal process.)"
                session["awaiting_user_info"] = True

        # Finally send response
        await ws.send_json({"type": "response", "message": clean_response})
        
    except Exception as e:
        logger.error(f"handle_chat error: {e}")
        try:
            await ws.send_json({"type": "response", "message": f"Sorry, something went wrong: {str(e)[:100]}"})
        except:
            pass


def get_optout_sites():
    """Return list of ALL opt-out sites to process (from sites.js)."""
    # ALL SITES with valid opt-out URLs - 119 total
    return [
        # === FREE SITES (59 sites) ===
        {"name": "truepeoplesearch.com", "opt_out_url": "https://www.truepeoplesearch.com/removal"},
        {"name": "fastpeoplesearch.com", "opt_out_url": "https://www.fastpeoplesearch.com/optout"},
        {"name": "thatsthem.com", "opt_out_url": "https://thatsthem.com/optout"},
        {"name": "zabasearch.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "peoplesearchnow.com", "opt_out_url": "https://www.peoplesearchnow.com/opt-out"},
        {"name": "searchpeoplefree.com", "opt_out_url": "https://www.searchpeoplefree.com/opt-out"},
        {"name": "usphonebook.com", "opt_out_url": "https://www.usphonebook.com/opt-out"},
        {"name": "anywho.com", "opt_out_url": "https://www.anywho.com/privacy"},
        {"name": "radaris.com", "opt_out_url": "https://radaris.com/control-privacy"},
        {"name": "smartbackgroundchecks.com", "opt_out_url": "https://www.smartbackgroundchecks.com/optout"},
        {"name": "whocalld.com", "opt_out_url": "https://whocalld.com/"},
        {"name": "allpeople.com", "opt_out_url": "https://allpeople.com/removal"},
        {"name": "familytreenow.com", "opt_out_url": "https://www.familytreenow.com/optout"},
        {"name": "castrickclues.com", "opt_out_url": "https://castrickclues.com/"},
        {"name": "spydialer.com", "opt_out_url": "https://www.spydialer.com/Consumers/"},
        {"name": "numlookup.com", "opt_out_url": "https://www.numlookup.com/opt_out"},
        {"name": "ipqualityscore.com", "opt_out_url": "https://www.ipqualityscore.com/privacy-policy"},
        {"name": "searchquarry.com", "opt_out_url": "https://privacyportal-eu.onetrust.com/webform/f6adb000-5a85-4ec1-a631-151c15d9d854/c3726644-a419-4170-86d8-9dfea2e9ef72"},
        {"name": "youmail.com", "opt_out_url": "https://compliance.youmail.com/submit-request"},
        {"name": "nuwber.com", "opt_out_url": "https://nuwber.com/removal/link"},
        {"name": "411.info", "opt_out_url": "https://411.info/manage/"},
        {"name": "addresses.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "addresssearch.com", "opt_out_url": "https://www.addresssearch.com/remove-info.php"},
        {"name": "advancedbackgroundchecks.com", "opt_out_url": "https://www.advancedbackgroundchecks.com/removal"},
        {"name": "acxiom.com", "opt_out_url": "https://www.acxiom.com/optout/"},
        {"name": "usa-official.com", "opt_out_url": "https://usa-official.com/remove.php"},
        {"name": "checksecrets.com", "opt_out_url": "https://www.checksecrets.com/optOut/name/landing"},
        {"name": "peoplesearch123.com", "opt_out_url": "https://www.peoplesearch123.com/optOut/name/landing"},
        {"name": "backgroundcheckers.net", "opt_out_url": "https://www.backgroundcheckers.net/optOut/name/landing"},
        {"name": "mugshotlook.com", "opt_out_url": "https://www.mugshotlook.com/optOut/name/landingPage"},
        {"name": "inmatessearcher.com", "opt_out_url": "https://www.inmatessearcher.com/optOut/name/landing"},
        {"name": "peoplesearchusa.org", "opt_out_url": "https://www.peoplesearchusa.org/optOut/name/landing"},
        {"name": "sealedrecords.net", "opt_out_url": "https://www.sealedrecords.net/optOut/name/landing"},
        {"name": "privatereports.com", "opt_out_url": "https://www.privatereports.com/optOut/name/landingPage"},
        {"name": "secretinfo.org", "opt_out_url": "https://www.secretinfo.org/optOut/name/landing"},
        {"name": "publicsearcher.com", "opt_out_url": "https://www.publicsearcher.com/optOut/name/landingPage"},
        {"name": "personsearchers.com", "opt_out_url": "https://www.personsearchers.com/optOut/name/landing"},
        {"name": "weinform.org", "opt_out_url": "https://www.weinform.org/opt_out/name/landing_page"},
        {"name": "truthrecord.org", "opt_out_url": "https://www.truthrecord.org/opt_out/name/landing_page"},
        {"name": "usa-people-search.com", "opt_out_url": "https://www.usa-people-search.com/removal"},
        {"name": "cyberbackgroundchecks.com", "opt_out_url": "https://www.cyberbackgroundchecks.com/removal"},
        {"name": "fastbackgroundcheck.com", "opt_out_url": "https://www.fastbackgroundcheck.com/optout"},
        {"name": "cellrevealer.com", "opt_out_url": "https://www.cellrevealer.com/Contact"},
        {"name": "callercenter.com", "opt_out_url": "https://www.callercenter.com/remove_name.htm"},
        {"name": "onlinesearches.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "veripages.com", "opt_out_url": "https://veripages.com/inner/removal-service?s=footer"},
        {"name": "centeda.com", "opt_out_url": "https://centeda.com/control/privacy"},
        {"name": "neighbor.report", "opt_out_url": "https://neighbor.report/remove"},
        {"name": "clustrmaps.com", "opt_out_url": "https://clustrmaps.com/bl/opt-out"},
        {"name": "24counter.com", "opt_out_url": "https://24counter.com/opt-out"},
        {"name": "officialusa.com", "opt_out_url": "https://www.officialusa.com/opt-out/"},
        {"name": "yankeegroup.com", "opt_out_url": "https://www.yankeegroup.com/optout/"},
        {"name": "simplecontacts.com", "opt_out_url": "https://www.simplecontacts.com/opt-out"},
        {"name": "freepeopledirectory.com", "opt_out_url": "https://www.spokeo.com/privacy/control"},
        {"name": "phonebooks.com", "opt_out_url": "https://www.phonebooks.com/opt-out"},
        {"name": "nationalpublicdata.com", "opt_out_url": "https://nationalpublicdata.com/optout.html"},
        
        # === PAID SITES (60 sites) ===
        {"name": "lookups.io", "opt_out_url": "https://lookups.io/"},
        {"name": "intelius.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "beenverified.com", "opt_out_url": "https://www.beenverified.com/app/optout/search"},
        {"name": "spokeo.com", "opt_out_url": "https://www.spokeo.com/opt_out/new"},
        {"name": "peoplefinders.com", "opt_out_url": "https://www.peoplefinders.com/opt-out"},
        {"name": "peoplefinder.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "instantcheckmate.com", "opt_out_url": "https://www.instantcheckmate.com/opt-out/"},
        {"name": "whitepages.com", "opt_out_url": "https://www.whitepages.com/suppression_requests"},
        {"name": "peoplesmart.com", "opt_out_url": "https://www.peoplesmart.com/optout"},
        {"name": "peoplelooker.com", "opt_out_url": "https://www.peoplelooker.com/optout"},
        {"name": "findpeoplefast.net", "opt_out_url": "https://findpeoplefast.net/remove-my-info"},
        {"name": "411.com", "opt_out_url": "https://www.411.com/opt-out"},
        {"name": "numberguru.com", "opt_out_url": "https://www.numberguru.com/svc/optout/search/optouts"},
        {"name": "infotracer.com", "opt_out_url": "https://infotracer.com/optout/"},
        {"name": "callersmart.com", "opt_out_url": "https://www.callersmart.com/optout"},
        {"name": "reversephonecheck.com", "opt_out_url": "https://www.reversephonecheck.com/optout/"},
        {"name": "whoeasy.com", "opt_out_url": "https://www.whoeasy.com/optout"},
        {"name": "nationalcellulardirectory.com", "opt_out_url": "https://www.nationalcellulardirectory.com/optout/"},
        {"name": "claritycheck.com", "opt_out_url": "https://claritycheck.com/help/delete-your-account"},
        {"name": "checkpeople.com", "opt_out_url": "https://checkpeople.com/opt-out"},
        {"name": "confidentialphonelookup.com", "opt_out_url": "https://www.confidentialphonelookup.com/contact/"},
        {"name": "peoplesearcher.com", "opt_out_url": "https://www.peoplesearcher.com/optOut/name/landing"},
        {"name": "privaterecords.net", "opt_out_url": "https://www.privaterecords.net/optOut/name/landing"},
        {"name": "recordsfinder.com", "opt_out_url": "http://recordsfinder.com/optout/"},
        {"name": "idstrong.com", "opt_out_url": "https://www.idstrong.com/privacyform/"},
        {"name": "courtcasefinder.com", "opt_out_url": "https://members.courtcasefinder.com/privacyform"},
        {"name": "freepeoplesearch.com", "opt_out_url": "https://freepeoplesearch.com/opt-out"},
        {"name": "spyfly.com", "opt_out_url": "https://www.spyfly.com/help-center/privacy-requests"},
        {"name": "information.com", "opt_out_url": "https://information.com/privacy-rights/"},
        {"name": "kidslivesafe.com", "opt_out_url": "https://www.kidslivesafe.com/help-center/privacy-requests"},
        {"name": "searchpublicrecords.com", "opt_out_url": "https://www.searchpublicrecords.com/help-center/privacy-requests"},
        {"name": "publicdatacheck.com", "opt_out_url": "https://www.publicdatacheck.com/help-center/privacy-requests"},
        {"name": "publicinfoservices.com", "opt_out_url": "https://www.publicinfoservices.com/help-center/privacy-requests"},
        {"name": "publicrecords.info", "opt_out_url": "https://dashboard.publicrecords.info/opt-out"},
        {"name": "publicrecordreports.com", "opt_out_url": "https://www.publicrecordreports.com/help-center/privacy-requests"},
        {"name": "propertyrecord.com", "opt_out_url": "https://dashboard.propertyrecord.com/opt-out"},
        {"name": "courtrec.com", "opt_out_url": "https://dashboard.courtrec.com/opt-out"},
        {"name": "courtrecords.us", "opt_out_url": "https://courtrecords.us/privacyform/"},
        {"name": "parkindatagroup.com", "opt_out_url": "https://dashboard.parkindatagroup.com/opt-out"},
        {"name": "propertyrecs.com", "opt_out_url": "https://dashboard.propertyrecs.com/opt-out"},
        {"name": "propertyrec.com", "opt_out_url": "https://dashboard.propertyrec.com/opt-out"},
        {"name": "publicrecords.us", "opt_out_url": "https://dashboard.publicrecords.us/opt-out"},
        {"name": "statecourts.org", "opt_out_url": "https://www.statecourts.org/privacyform/"},
        {"name": "reversephonelookup.com", "opt_out_url": "https://www.intelius.com/privacy-center/"},
        {"name": "usatrace.com", "opt_out_url": "https://www.usatrace.com/your-privacy/"},
        {"name": "quickpeopletrace.com", "opt_out_url": "https://www.quickpeopletrace.com/contact-us/"},
        {"name": "truthfinder.com", "opt_out_url": "https://www.truthfinder.com/privacy-center/"},
        {"name": "ussearch.com", "opt_out_url": "https://www.ussearch.com/privacy-center"},
        {"name": "peoplewin.com", "opt_out_url": "https://www.spokeo.com/optout"},
        {"name": "yellowbook.com", "opt_out_url": "https://hibu.com/legal/privacy-form"},
        {"name": "publicrecords.searchsystems.net", "opt_out_url": "https://www.beenverified.com/app/optout/search"},
        {"name": "neighborwho.com", "opt_out_url": "https://www.neighborwho.com/svc/optout/search/optouts"},
        {"name": "ownerly.com", "opt_out_url": "https://www.ownerly.com/svc/optout/search/optouts"},
        {"name": "bumper.com", "opt_out_url": "https://www.bumper.com/svc/optout/search/comprehensive_optouts"},
        {"name": "staterecords.org", "opt_out_url": "https://staterecords.org/optout"},
        {"name": "mylife.com", "opt_out_url": "https://www.mylife.com/ccpa/index.pubview"},
        {"name": "mypropertyrecs.com", "opt_out_url": "https://dashboard.mypropertyrecs.com/opt-out"},
    ]



async def extract_user_info(message: str) -> dict:
    """Extract name and address components from a user message with smart parsing."""
    result = {k: "" for k in ["first_name", "last_name", "street", "apt", "city", "state", "zip", "address"]}
    
    # Try to extract name with various patterns
    for pattern in EXTRACTION_PATTERNS["name"]:
        match = re.search(pattern, message)
        if match:
            first, last = match.group(1).strip(), match.group(2).strip()
            # Make sure neither word is a street type
            if first.lower() not in EXTRACTION_PATTERNS["street_types"] and last.lower() not in EXTRACTION_PATTERNS["street_types"]:
                result["first_name"], result["last_name"] = first.title(), last.title()
                break
    
    # Fallback name extraction: find two capitalized words NOT part of an address
    if not result["first_name"]:
        parts = message.split(',')[0].split()
        for i, word in enumerate(parts):
            if i + 1 < len(parts) and len(word) > 1 and word[0].isupper() and len(parts[i+1]) > 1 and parts[i+1][0].isupper():
                skip = {"my", "the", "and", "address", "is", "at", "in", "to", "for", "remove", "help", "data"} | EXTRACTION_PATTERNS["street_types"]
                if word.lower() not in skip and parts[i+1].lower() not in skip and not any(c.isdigit() for c in word + parts[i+1]):
                    result["first_name"], result["last_name"] = word.title(), parts[i+1].title()
                    break
    
    # Clean up multi-line addresses (remove country references)
    cleaned_message = message
    for pattern in EXTRACTION_PATTERNS["country"]:
        cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE)
    
    # Parse multi-line format
    lines = [l.strip() for l in cleaned_message.split('\n') if l.strip()]
    if len(lines) >= 2:
        street_line, csz_line = None, None
        for line in lines:
            if re.match(r'^\d+\s+', line) and not street_line: street_line = line
            elif re.search(r'\b[A-Z]{2}\s+\d{5}\b', line) and not csz_line: csz_line = line
        
        if street_line:
            apt_match = re.search(EXTRACTION_PATTERNS["apt_keywords"], street_line, re.IGNORECASE)
            if apt_match:
                result["street"], result["apt"] = apt_match.group(1).strip(), f"{apt_match.group(2)} {apt_match.group(3)}".strip()
            else:
                result["street"] = street_line.strip()
        
        if csz_line:
            csz_match = re.search(r'^(.+?)(?:,|\s+)([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', csz_line)
            if csz_match:
                result["city"], result["state"], result["zip"] = csz_match.group(1).strip().title(), csz_match.group(2).upper(), csz_match.group(3)
        
        if result["street"] and result["city"] and result["state"]:
            result["address"] = f"{result['street']}{' ' + result['apt'] if result['apt'] else ''}, {result['city']}, {result['state']} {result['zip']}".strip()
            return result
    
    # Single-line pattern: "123 Street Name, City, ST 12345"
    full_addr_pattern = r'(\d+\s+[^,]+?)(?:\s*,\s*)([A-Za-z\s]+?)(?:\s*,\s*)([A-Z]{2})\s*(\d{5}(?:-\d{4})?)'
    match = re.search(full_addr_pattern, cleaned_message)
    if match:
        street_raw = match.group(1).strip()
        result["city"], result["state"], result["zip"] = match.group(2).strip().title(), match.group(3).upper(), match.group(4).strip()
        apt_match = re.search(EXTRACTION_PATTERNS["apt_keywords"], street_raw, re.IGNORECASE)
        if apt_match:
            result["street"], result["apt"] = apt_match.group(1).strip(), f"{apt_match.group(2)} {apt_match.group(3)}".strip()
        else:
            result["street"] = street_raw
        result["address"] = f"{result['street']}{' ' + result['apt'] if result['apt'] else ''}, {result['city']}, {result['state']} {result['zip']}".strip()
    else:
        # Simple/Partial extraction
        zip_match = re.search(r'(\d{5}(?:-\d{4})?)', message)
        if zip_match: result["zip"] = zip_match.group(1)
        for word in message.replace(',', ' ').split():
            if word.upper() in US_STATES:
                result["state"] = word.upper()
                break
        street_match = re.search(r'(\d+\s+[A-Za-z0-9\s]+(?:St|Street|Dr|Drive|Ave|Avenue|Blvd|Boulevard|Rd|Road|Lane|Ln|Way|Court|Ct|Circle|Cir|Place|Pl)\.?)(?:\s+(?:Apt|Apartment|Unit|Suite|Ste|#)[\s\.]*([A-Za-z0-9\-]+))?', message, re.IGNORECASE)
        if street_match:
            result["street"], result["apt"] = street_match.group(1).strip(), (street_match.group(2).strip() if street_match.group(2) else "")
        if result["state"]:
            city_match = re.search(rf'([A-Za-z\s]+?)[\s,]+{result["state"]}', message, re.IGNORECASE)
            if city_match:
                result["city"] = re.sub(r'\b(St|Street|Dr|Drive|Ave|Avenue|Blvd|Boulevard|Rd|Road|Lane|Ln|Way|Court|Ct)\b', '', city_match.group(1), flags=re.IGNORECASE).strip().split(',')[-1].strip().title()
        if result["street"]:
            result["address"] = f"{result['street']}{' ' + result['apt'] if result['apt'] else ''}, {result['city'] or ''}, {result['state'] or ''} {result['zip'] or ''}".replace(' ,', '').strip()
    
    return result


# Static File Serving
PROJECT_ROOT = Path(__file__).parent.parent
@app.get("/")
async def serve_index(): return FileResponse(PROJECT_ROOT / "index.html")
@app.get("/{filename:path}")
async def serve_static(filename: str):
    f = PROJECT_ROOT / filename
    if f.exists() and f.is_file(): return FileResponse(f)
    return FileResponse(PROJECT_ROOT / "index.html") # Fallback to index for SPA

if __name__ == "__main__":
    import uvicorn
    # Final sweep to catch any late-initializing loggers
    setup_all_loggers()
    uvicorn.run(app, host="127.0.0.1", port=3000, log_config=None)
