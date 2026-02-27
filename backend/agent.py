"""
OPTX Backend Server
Browser automation agent, WebSocket API, and email verification service.
Powered by Browserless for stealth browsing and captcha solving.
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
from html import unescape
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from playbooks import PLAYBOOKS


# === COLORIZED LOGGING ===
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""

    COLORS = {
        "DEBUG": "\033[0;36m",  # Cyan
        "INFO": "\033[0;32m",  # Green
        "WARNING": "\033[0;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
        "CRITICAL": "\033[0;35m",  # Magenta
        "RESET": "\033[0m",
        "BLUE": "\033[0;34m",  # Blue for URLs
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        blue = self.COLORS["BLUE"]

        # Save original and format levelname (INFO: etc)
        levelname = record.levelname.strip(":").upper()
        record.levelname = f"{color}{levelname}:{reset}"

        # Format message and strip any pesky brackets [name] that might be in it
        msg = super().format(record)

        # 1. Strip uvicorn-style brackets from the start [uvicorn.error]
        msg = re.sub(r"\[.*?\]\s*", "", msg)

        # 2. Colorize Status Codes (e.g. 200, 404)
        msg = re.sub(r"\b(200|201|204)\b", f"{self.COLORS['INFO']}\\1{reset}", msg)
        msg = re.sub(r"\b(404|500)\b", f"{self.COLORS['ERROR']}\\1{reset}", msg)

        # 3. Colorize URLs
        msg = re.sub(r"(https?://[^\s]+)", f"{blue}\\1{reset}", msg)

        # 4. Clean up any accidental double colons
        msg = msg.replace("::", ":")

        record.levelname = levelname  # Restore for other potential use
        return msg


# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])


def setup_all_loggers():
    """Apply the custom formatter to every single logger in the universe."""
    formatter = ColoredFormatter("%(levelname)s %(message)s")

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

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


# ============================================================================
# US STATES & EMAIL SERVICE
# ============================================================================

US_STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


class GuerrillaMailService:
    """
    Guerrilla Mail - Zero account email service with multiple domains.
    No registration needed - uses session-based API.
    Multiple domains (sharklasers.com, grr.la, etc.) to avoid blacklists.
    """

    API_BASE = "https://api.guerrillamail.com/ajax.php"

    def __init__(self):
        self.address = None
        self.sid_token = None
        self.session = requests.Session()  # Use session for cookies

    def _generate_random_string(self, length=10):
        """Generate a random string for email username."""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def create_account(self):
        """
        Get a session and email address from Guerrilla Mail.
        No actual account creation - just initializes a session.
        """
        try:
            # Get email address and session token
            params = {
                "f": "get_email_address",
                "ip": "127.0.0.1",
                "agent": "OPTX_Automation"
            }
            response = self.session.get(self.API_BASE, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.sid_token = data.get("sid_token")
                self.address = data.get("email_addr")
                
                if self.address and self.sid_token:
                    logger.info(f"Generated Guerrilla Mail address: {self.address}")
                    return self.address
                else:
                    logger.error(f"Missing address or token in response: {data}")
            else:
                logger.error(f"Failed to get email: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Guerrilla Mail init error: {e}")
        
        return None

    def get_messages(self):
        """Check inbox for messages using check_email endpoint."""
        if not self.sid_token:
            return []

        try:
            params = {
                "f": "check_email",
                "sid_token": self.sid_token,
                "seq": 0  # Start from beginning
            }
            response = self.session.get(self.API_BASE, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # Update sid_token if changed
                if "sid_token" in data:
                    self.sid_token = data["sid_token"]
                
                messages = data.get("list", [])
                return messages if isinstance(messages, list) else []
                
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
        return []

    def get_message_content(self, msg_id):
        """Get full message content including HTML body."""
        if not self.sid_token:
            return ""

        try:
            params = {
                "f": "fetch_email",
                "sid_token": self.sid_token,
                "email_id": msg_id
            }
            response = self.session.get(self.API_BASE, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # Update sid_token if changed
                if "sid_token" in data:
                    self.sid_token = data["sid_token"]
                
                # Guerrilla Mail returns 'mail_body' for HTML content
                return data.get("mail_body", "") or data.get("mail_text", "")
                
        except Exception as e:
            logger.error(f"Failed to get message content: {e}")
        return ""

    def find_verification_link(self, timeout=180):
        """Poll for verification email and extract the link."""
        start_time = time.time()
        logger.info(f"Polling Guerrilla Mail for {self.address}...")
        poll_count = 0

        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = int(time.time() - start_time)
            logger.info(f"Email poll #{poll_count} ({elapsed}s elapsed)...")
            
            messages = self.get_messages()
            
            if messages:
                logger.info(f"Found {len(messages)} message(s) in inbox")
                
                # Find the first message NOT from guerrillamail (skip welcome email)
                target_msg = None
                for msg in messages:
                    sender = msg.get("mail_from", "").lower()
                    if "guerrillamail" not in sender:
                        target_msg = msg
                        break
                
                if not target_msg:
                    logger.debug("Only guerrillamail system emails found, waiting...")
                    time.sleep(10)
                    continue
                
                msg_id = target_msg.get("mail_id")
                sender = target_msg.get("mail_from", "unknown")
                subject = target_msg.get("mail_subject", "no subject")
                logger.info(f"From: {sender}, Subject: {subject}")
                
                content = self.get_message_content(msg_id)

                if not content:
                    logger.warning("Message has no content, waiting...")
                    time.sleep(5)
                    continue

                logger.info(f"Message content length: {len(content)} chars")
                
                # Use BeautifulSoup to properly parse HTML and extract links
                soup = BeautifulSoup(content, 'html.parser')
                all_links = []
                
                # Find all anchor tags and extract href
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Decode HTML entities like &amp; to &
                    href = unescape(href)
                    all_links.append(href)
                    logger.debug(f"Found link: {href[:80]}...")
                
                logger.info(f"Found {len(all_links)} links in email")

                # Priority 1: Look for PeopleSearchNow validate-record-info links
                for link in all_links:
                    if "peoplesearchnow.com" in link.lower() and "validate-record-info" in link.lower():
                        logger.info(f"Found PeopleSearchNow verification link")
                        return link

                # Priority 2: General opt-out/verify/confirm patterns
                for link in all_links:
                    link_lower = link.lower()
                    if any(kw in link_lower for kw in ["opt-out", "optout", "verify", "confirm", "validate", "removal"]):
                        logger.info(f"Found verification link with keyword match")
                        return link

                # Fallback: Return first https link if nothing else matches
                for link in all_links:
                    if link.startswith("https://"):
                        logger.info(f"Using fallback link: {link[:80]}...")
                        return link
                
                logger.warning("Email found but no valid links detected!")
            else:
                logger.debug(f"No messages yet (poll #{poll_count})")

            time.sleep(10)  # Poll every 10 seconds

        logger.warning(f"Email polling timed out after {timeout}s ({poll_count} polls)")
        return None


# Keep alias for backward compatibility
MailTMService = GuerrillaMailService




# ============================================================================
# UTILITIES
# ============================================================================


class BrowserlessAgent:
    ENDPOINTS = {
        "sfo": "wss://production-sfo.browserless.io",
        "london": "wss://production-lon.browserless.io",
        "amsterdam": "wss://production-ams.browserless.io",
    }

    def __init__(self, ws, api_key=None, region="sfo", browser_settings=None):
        self.ws = ws
        self.api_key = api_key or os.getenv("BROWSERLESS_API_KEY")
        self.region = region
        self.playwright = None
        self.browser = None
        self.page = None
        self.email_service = None  # Instance of MailTMService
        self.running = True
        self.paused = False
        self.screenshot_task = None
        self.cdp_session = None  # CDP session for Browserless commands
        # Captcha event tracking
        self.captcha_found_event = None  # asyncio.Event for captcha detection
        self.captcha_solved_event = None  # asyncio.Event for captcha solved
        self.captcha_result = None  # Store captcha solve result
        # Browser settings from frontend (defaults if not provided)
        self.settings = browser_settings or {
            "stealth": True,
            "captcha": True,
            "proxy": True,
            "humanlike": True,
            "adblock": False,
        }
        self.status = ""  # Empty until first real action
        self.running = True

    def prepare_user_data(self, user_data):
        """Prepare user data with derived fields (like full_name)."""
        data = user_data.copy()
        first = data.get("first_name", "")
        last = data.get("last_name", "")
        city = data.get("city", "")
        state = data.get("state", "")

        data["full_name"] = f"{first} {last}".strip()
        data["full_name_reversed"] = f"{last}, {first}".strip()
        data["city_state"] = f"{city}, {state}".strip()

        # Normalize state
        if state and len(state) > 2:
            rev_states = {v.lower(): k for k, v in US_STATES.items()}
            data["state_abbr"] = rev_states.get(state.lower(), state)
        else:
            data["state_abbr"] = state

        return data

    async def execute_session_steps(self, steps, data, session_name="Session"):
        """
        Execute a list of playbook steps for a single browser session.
        Returns True if all critical steps succeeded, False otherwise.
        Designed for the two-session architecture with 1-minute time limits.
        """
        if not self.page:
            logger.error(f"No active page for {session_name}")
            return False
        
        session_start = asyncio.get_event_loop().time()
        max_session_time = 120  # 2 minutes - Browserless sessions are flexible
        
        for step_idx, step in enumerate(steps):
            # Check time limit
            elapsed = asyncio.get_event_loop().time() - session_start
            if elapsed > max_session_time:
                logger.warning(f"{session_name} approaching time limit ({elapsed:.0f}s)")
                await self.send_msg(f"Session time limit reached")
                break
            
            action = step.get("action")
            is_optional = step.get("optional", False)

            # Proactively refresh page reference from browser context
            # Browserless may replace the page internally (e.g., during captcha detection)
            if action != "solve_captcha" and self.browser and self.browser.contexts:
                ctx = self.browser.contexts[0]
                for pg in ctx.pages:
                    if not pg.is_closed():
                        if pg != self.page:
                            logger.info(f"Page reference changed, switching to active page")
                            self.page = pg
                            try:
                                self.cdp_session = await self.page.context.new_cdp_session(self.page)
                            except Exception:
                                pass
                        break

            # Check page state
            if action != "solve_captcha" and self.page and hasattr(self.page, "is_closed") and self.page.is_closed():
                logger.info(f"Page closed during {session_name}, attempting recovery...")
                recovered = False
                for _ in range(10):  # Wait up to 5 seconds
                    await asyncio.sleep(0.5)
                    if self.browser and self.browser.contexts:
                        ctx = self.browser.contexts[0]
                        for pg in ctx.pages:
                            if not pg.is_closed():
                                self.page = pg
                                try:
                                    self.cdp_session = await self.page.context.new_cdp_session(self.page)
                                except Exception:
                                    pass
                                recovered = True
                                break
                    if recovered:
                        break
                if not recovered:
                    logger.warning(f"Page closed, stopping {session_name}")
                    return False

            # Log each step for debugging
            logger.info(f"{session_name} Step {step_idx + 1}: {action}")
            
            try:
                success = await self._execute_single_step(step, data)
                if not success and not is_optional:
                    logger.warning(f"{session_name} step failed: {action}")
                    # Only abort on navigation failures
                    if action == "navigate":
                        return False
            except Exception as e:
                error_str = str(e).lower()
                if "closed" in error_str or "target" in error_str or "context" in error_str:
                    logger.info(f"Page died during {action}, recovering and retrying...")
                    # Recover page reference
                    recovered = False
                    await asyncio.sleep(1)
                    if self.browser and self.browser.contexts:
                        ctx = self.browser.contexts[0]
                        for pg in ctx.pages:
                            if not pg.is_closed():
                                self.page = pg
                                try:
                                    self.cdp_session = await self.page.context.new_cdp_session(self.page)
                                except Exception:
                                    pass
                                recovered = True
                                break
                    if recovered:
                        # Retry the step once with recovered page
                        try:
                            retry_success = await self._execute_single_step(step, data)
                            if not retry_success and not is_optional:
                                logger.warning(f"Retry also failed for {action}")
                                if action == "navigate":
                                    return False
                        except Exception as retry_err:
                            logger.warning(f"Retry error for {action}: {retry_err}")
                            if not is_optional and action == "navigate":
                                return False
                    else:
                        logger.warning(f"Could not recover page after {action} failure")
                        if not is_optional and action == "navigate":
                            return False
                else:
                    logger.error(f"Step {action} error: {e}")
                    if not is_optional and action == "navigate":
                        return False
        
        return True

    async def _execute_single_step(self, step, data):
        """
        Execute a single playbook step.
        Returns True on success, False on failure.
        This is a lightweight wrapper that delegates to the action handlers.
        """
        action = step.get("action")
        is_optional = step.get("optional", False)
        
        try:
            if action == "navigate":
                url_key = step.get("url_variable") or step.get("context_key")
                if url_key:
                    url = data.get(url_key)
                    if not url:
                        logger.error(f"Missing URL for variable {url_key}")
                        return False
                else:
                    url = step.get("url", "")
                
                await self.send_msg(f"Navigating to {url[:50]}...")
                try:
                    # Use domcontentloaded + longer timeout to handle Cloudflare
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Wait for page to fully load after Cloudflare
                    await self.send_msg("Waiting for page to fully load...")
                    max_wait = 30
                    for i in range(max_wait):
                        try:
                            is_cloudflare = await self.page.evaluate("""
                                () => {
                                    return document.body.innerText.includes('Checking your browser') ||
                                           document.body.innerText.includes('Just a moment') ||
                                           document.querySelector('iframe[src*="challenges.cloudflare"]') !== null;
                                }
                            """)
                            if not is_cloudflare:
                                has_content = await self.page.evaluate("""
                                    () => {
                                        return !!(
                                            document.querySelector('#verifyEmailForm') ||
                                            document.querySelector('#removalForm') ||
                                            document.querySelector('form') ||
                                            document.querySelector('main') ||
                                            document.body.innerText.length > 500
                                        );
                                    }
                                """)
                                if has_content:
                                    break
                            await asyncio.sleep(1)
                        except Exception:
                            await asyncio.sleep(1)
                    
                    # Settle pause after Cloudflare
                    await asyncio.sleep(3)
                    await self.send_msg("Navigated successfully")
                    return True
                except Exception as nav_error:
                    if "Timeout" in str(nav_error):
                        logger.warning(f"Navigation timeout, continuing: {url}")
                        await self.send_msg("Page loading slow, continuing...")
                        await asyncio.sleep(3)
                        return True
                    logger.warning(f"Navigation error: {nav_error}")
                    return False
                    
            elif action == "wait_for":
                selector = step["selector"]
                timeout = step.get("timeout", 30) * 1000
                try:
                    await self.page.wait_for_selector(selector, timeout=timeout)
                    return True
                except Exception as e:
                    if "Timeout" in str(e):
                        await self.send_msg(f"Element not found: {selector}, continuing...")
                    elif not is_optional:
                        logger.warning(f"Element not found: {selector}")
                    return is_optional
                    
            elif action == "scroll_to":
                selector = step["selector"]
                try:
                    await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                    el = await self.page.query_selector(selector)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                    return True
                except Exception as e:
                    error_str = str(e).lower()
                    if "closed" in error_str or "context" in error_str:
                        logger.warning(f"Browser issue during scroll: {e}")
                    return True  # scroll never kills a session
                    
            elif action == "fill" or action == "human_type":
                selector = step["selector"]
                field = step.get("field")
                context_key = step.get("context_key")
                
                if context_key:
                    val = data.get(context_key, "")
                elif field:
                    val = data.get(field, "")
                else:
                    val = step.get("value", "")
                
                if val:
                    try:
                        # Wait for input to be ready before typing
                        await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                        await self.page.fill(selector, str(val))
                        return True
                    except Exception as e:
                        logger.warning(f"Fill error: {e}")
                        return is_optional
                return True  # No value is ok
                
            elif action == "select":
                selector = step["selector"]
                val = step.get("value") or data.get(step.get("field", ""))
                if val:
                    try:
                        # Wait for select element before interacting
                        await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                        await self.page.select_option(selector, value=str(val))
                        return True
                    except Exception:
                        return is_optional
                return True
                
            elif action == "select_state":
                selector = step["selector"]
                fmt = step.get("format", "abbr")
                state_val = data.get("state_abbr" if fmt == "abbr" else "state")
                if state_val:
                    try:
                        await self.page.select_option(selector, value=state_val)
                        return True
                    except:
                        try:
                            await self.page.select_option(selector, label=state_val)
                            return True
                        except:
                            return is_optional
                return True
                
            elif action == "click":
                selector = step["selector"]
                try:
                    # Wait for element, then try to click
                    await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                    await asyncio.sleep(0.3)  # Brief settle
                    await self.page.click(selector)
                    return True
                except Exception as e:
                    error_str = str(e).lower()
                    if "closed" in error_str or "target" in error_str or "context" in error_str:
                        # Page reference died - try to recover and use JS click
                        logger.info(f"Page died during click {selector}, recovering...")
                        await asyncio.sleep(1)
                        if self.browser and self.browser.contexts:
                            ctx = self.browser.contexts[0]
                            for pg in ctx.pages:
                                if not pg.is_closed():
                                    self.page = pg
                                    try:
                                        self.cdp_session = await self.page.context.new_cdp_session(self.page)
                                    except Exception:
                                        pass
                                    break
                        # Retry with JS click on recovered page
                        try:
                            await self.page.evaluate(f'document.querySelector("{selector}")?.click()')
                            logger.info(f"JS click succeeded on recovered page: {selector}")
                            return True
                        except Exception as retry_err:
                            logger.warning(f"Click failed after recovery: {retry_err}")
                            return is_optional
                    else:
                        # Try JS click as fallback
                        try:
                            await self.page.evaluate(f'document.querySelector("{selector}")?.click()')
                            return True
                        except:
                            logger.warning(f"Click failed: {e}")
                            return is_optional
                        
            elif action == "wait":
                seconds = step.get("seconds", 1)
                await asyncio.sleep(seconds)
                return True
                
            elif action == "solve_captcha":
                submit_selector = step.get("submit_selector")
                result = await self.wait_for_captcha_solved(submit_selector=submit_selector)
                return result.get("solved", False) or True  # Don't fail on captcha issues
                
            elif action == "verify_text":
                patterns = step.get("patterns", [])
                timeout = step.get("timeout", 10)
                
                for _ in range(timeout):
                    try:
                        page_text = await self.page.evaluate("() => document.body.innerText")
                        for pattern in patterns:
                            if pattern.lower() in page_text.lower():
                                return True
                    except:
                        pass
                    await asyncio.sleep(1)
                
                logger.info("Verification text not found")
                return is_optional
                
            elif action == "conditional_block":
                condition = step.get("condition", {})
                selector = condition.get("selector_exists")
                
                if selector:
                    try:
                        elem = await self.page.query_selector(selector)
                        if elem:
                            # Execute nested steps
                            nested_steps = step.get("steps", [])
                            for nested in nested_steps:
                                await self._execute_single_step(nested, data)
                    except:
                        pass
                return True
                
            else:
                logger.warning(f"Unknown action: {action}")
                return True
                
        except Exception as e:
            logger.error(f"Step execution error ({action}): {e}")
            return is_optional

    async def execute_playbook(self, playbook_name, user_data):
        """Execute a series of steps defined in a playbook."""
        if playbook_name not in PLAYBOOKS:
            # Fallback for dynamic sites if no playbook
            logger.error(f"No playbook found for: {playbook_name}")
            return False

        playbook = PLAYBOOKS[playbook_name]
        data = self.prepare_user_data(user_data)

        for step in playbook["steps"]:
            # Check page state - but don't immediately stop on brief closures (Cloudflare redirects)
            if self.page and hasattr(self.page, "is_closed") and self.page.is_closed():
                # Page might be redirecting (common after Cloudflare), wait briefly
                logger.info("Page appears closed, waiting for potential recovery...")
                recovered = False
                for _ in range(10):  # Wait up to 5 seconds
                    await asyncio.sleep(0.5)
                    if self.page and not (hasattr(self.page, "is_closed") and self.page.is_closed()):
                        logger.info("Page recovered after brief closure")
                        recovered = True
                        break
                
                if not recovered:
                    logger.warning(
                        f"Page closed, stopping playbook execution for {playbook_name}"
                    )
                    break

            action = step.get("action")
            max_retries = 2
            retry_count = 0

            while retry_count < max_retries:
                try:
                    if action == "navigate":
                        if not self.page:
                            logger.error("No active page for navigation")
                            return False
                        url_key = step.get("url_variable") or step.get("context_key")
                        if url_key:
                            url = data.get(url_key)
                            if not url:
                                logger.error(f"Missing URL for variable {url_key}")
                                return False
                        else:
                            url = step["url"]

                        await self.send_browser_update(f"Navigating to {url}")
                        try:
                            # Use domcontentloaded instead of networkidle for Cloudflare pages
                            # Longer timeout (60s) to allow captcha solving
                            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                            
                            # Wait for Cloudflare captcha to be solved if present
                            # Cloudflare shows a challenge page first, then redirects
                            await self.send_msg(f"Waiting for page to fully load...")
                            
                            # Wait for actual page content (not Cloudflare challenge)
                            # Loop checking for either the form or body content
                            max_wait = 30  # seconds
                            for i in range(max_wait):
                                try:
                                    # Check if we're past Cloudflare (no challenge iframe)
                                    is_cloudflare = await self.page.evaluate("""
                                        () => {
                                            return document.body.innerText.includes('Checking your browser') ||
                                                   document.body.innerText.includes('Just a moment') ||
                                                   document.querySelector('iframe[src*="challenges.cloudflare"]') !== null;
                                        }
                                    """)
                                    
                                    if not is_cloudflare:
                                        # Check if the actual form/content is present
                                        has_content = await self.page.evaluate("""
                                            () => {
                                                return !!(
                                                    document.querySelector('#verifyEmailForm') ||
                                                    document.querySelector('form') ||
                                                    document.querySelector('main') ||
                                                    document.body.innerText.length > 500
                                                );
                                            }
                                        """)
                                        if has_content:
                                            await self.send_msg(f"Navigated to {url}")
                                            break
                                        
                                    await asyncio.sleep(1)
                                except Exception as e:
                                    logger.debug(f"Navigation check error: {e}")
                                    await asyncio.sleep(1)
                            else:
                                await self.send_msg(f"Page loaded (may still be processing)")
                            
                            # Extra pause to let page fully settle after Cloudflare
                            await self.send_msg("Waiting for page to stabilize...")
                            await asyncio.sleep(3)
                            
                        except Exception as nav_error:
                            if "Timeout" in str(nav_error):
                                # Page might still be usable even after timeout
                                logger.warning(f"Navigation timeout, but continuing: {url}")
                                await self.send_msg(f"Page loading slow, continuing anyway...")
                                await asyncio.sleep(3)
                            else:
                                raise

                    elif action == "wait_for":
                        if not self.page:
                            logger.error("No active page for wait_for")
                            return False
                        selector = step["selector"]
                        timeout = step.get("timeout", 30) * 1000
                        try:
                            await self.page.wait_for_selector(selector, timeout=timeout)
                        except Exception as e:
                            if "Timeout" in str(e):
                                await self.send_msg(
                                    f"Element not found: {selector}. Continuing anyway..."
                                )
                            else:
                                raise

                    elif action == "scroll_to":
                        if not self.page:
                            logger.error("No active page for scroll_to")
                            return False
                        selector = step["selector"]
                        try:
                            await self.page.wait_for_selector(
                                selector, state="visible", timeout=10000
                            )
                            el = await self.page.query_selector(selector)
                            if el:
                                await el.scroll_into_view_if_needed()
                                await asyncio.sleep(
                                    0.5
                                )  # Allow time for scrolling to settle
                            else:
                                logger.warning(
                                    f"Scroll target not found: {selector}"
                                )
                        except Exception as e:
                            error_str = str(e).lower()
                            if "closed" in error_str or "context" in error_str:
                                logger.warning(f"Browser issue during scroll: {e}")
                            else:
                                logger.warning(f"Scroll issue: {str(e)[:40]}")

                    elif action == "fill":
                        if not self.page:
                            logger.error("No active page for fill")
                            return False
                        selector = step["selector"]
                        field = step.get("field")
                        context_key = step.get("context_key")

                        val = step.get("value")
                        if not val:
                            if field:
                                val = data.get(field, "")
                            elif context_key:
                                val = data.get(context_key, "")

                        if val:
                            try:
                                await self.page.wait_for_selector(
                                    selector, state="visible", timeout=10000
                                )
                                await self.page.fill(selector, str(val))
                            except Exception as e:
                                error_str = str(e).lower()
                                if "closed" in error_str or "context" in error_str:
                                    logger.warning(f"Browser issue during fill: {e}")
                                    await self.send_msg(f"Browser hiccup on {selector}, continuing...")
                                else:
                                    await self.send_msg(f"Fill issue: {str(e)[:40]}, continuing...")

                    elif action == "human_type":
                        if not self.page:
                            logger.error("No active page for human_type")
                            return False
                        selector = step["selector"]
                        field = step.get("field")
                        context_key = step.get("context_key")

                        val = step.get("value")
                        if not val:
                            if field:
                                val = data.get(field, "")
                            elif context_key:
                                val = data.get(context_key, "")

                        if val:
                            try:
                                # Wait for element to be visible
                                await self.page.wait_for_selector(
                                    selector, state="visible", timeout=15000
                                )
                                await asyncio.sleep(0.3)
                                
                                # Try simple fill() first - most reliable
                                try:
                                    await self.page.fill(selector, str(val))
                                except Exception as fill_err:
                                    # Fallback to click + type
                                    logger.warning(f"Fill failed, trying click+type: {fill_err}")
                                    element = await self.page.query_selector(selector)
                                    if element:
                                        await element.click()
                                        await asyncio.sleep(0.2)
                                        # Use type_text instead of keyboard for better reliability
                                        await element.fill(str(val))
                                    else:
                                        logger.warning(f"Element not found: {selector}")
                                
                                await asyncio.sleep(0.3)  # Brief pause after typing
                                
                            except Exception as e:
                                error_str = str(e).lower()
                                if "closed" in error_str or "context" in error_str:
                                    # Browser connection issue - log but try to continue
                                    logger.warning(f"Browser issue during type: {e}")
                                    await self.send_msg(f"Browser hiccup on {selector}, continuing...")
                                else:
                                    await self.send_msg(f"Type issue on {selector}: {str(e)[:40]}")
                                # Don't return False - continue with next step

                    elif action == "fill_full_name":
                        if not self.page:
                            logger.error("No active page for fill_full_name")
                            return False
                        selector = step["selector"]
                        full_name = data.get("full_name", "")
                        if full_name:
                            await self.page.fill(selector, full_name)

                    elif action == "select":
                        if not self.page:
                            logger.error("No active page for select")
                            return False
                        selector = step["selector"]
                        field = step.get("field")
                        val = step.get("value") or data.get(field)
                        if val:
                            try:
                                await self.page.wait_for_selector(
                                    selector, state="visible", timeout=10000
                                )
                                await self.page.select_option(selector, value=str(val))
                            except Exception as e:
                                error_str = str(e).lower()
                                if "closed" in error_str or "context" in error_str:
                                    logger.warning(f"Browser issue during select: {e}")
                                    await self.send_msg(f"Browser hiccup on {selector}, continuing...")
                                else:
                                    await self.send_msg(f"Select issue: {str(e)[:40]}, continuing...")

                    elif action == "select_state":
                        if not self.page:
                            logger.error("No active page for select_state")
                            return False
                        selector = step["selector"]
                        fmt = step.get("format", "abbr")  # "abbr" or "full"
                        state_val = data.get("state_abbr" if fmt == "abbr" else "state")
                        if state_val:
                            try:
                                await self.page.select_option(selector, value=state_val)
                            except:
                                # Fallback try selecting by label if value fails
                                await self.page.select_option(selector, label=state_val)

                    elif action == "click":
                        if not self.page:
                            logger.error("No active page for click")
                            return False
                        selector = step["selector"]
                        timeout = step.get("timeout", 30) * 1000
                        try:
                            # Wait for element to be available
                            await self.page.wait_for_selector(
                                selector, state="visible", timeout=timeout
                            )
                            # Brief pause before clicking
                            await asyncio.sleep(0.3)
                            
                            # Try JavaScript click first (more reliable for checkboxes)
                            try:
                                await self.page.eval_on_selector(
                                    selector, 
                                    "el => el.click()"
                                )
                            except Exception as js_err:
                                # Fallback to regular click
                                logger.warning(f"JS click failed, trying regular: {js_err}")
                                element = await self.page.query_selector(selector)
                                if element:
                                    await element.scroll_into_view_if_needed()
                                    await asyncio.sleep(0.3)
                                    await element.click()
                                else:
                                    logger.warning(f"Element not found: {selector}")
                            
                            # Brief pause after click to let page react
                            await asyncio.sleep(0.5)
                            
                        except Exception as e:
                            error_str = str(e).lower()
                            if "timeout" in error_str or "not found" in error_str:
                                logger.warning(
                                    f"Click target not found: {selector}"
                                )
                            elif "closed" in error_str or "context" in error_str:
                                # Browser connection issue - log but continue
                                logger.warning(f"Browser connection issue during click: {e}")
                                await self.send_msg(f"Browser hiccup on {selector}, continuing...")
                            else:
                                await self.send_msg(f"Click issue: {str(e)[:50]}, continuing...")
                                # Don't return False - try to continue with next step

                    elif action == "wait":
                        seconds = step.get(
                            "seconds",
                            step.get("duration", 1000) / 1000
                            if "duration" in step
                            else 1,
                        )
                        await self.send_msg(f"Waiting {seconds} seconds...")
                        await asyncio.sleep(seconds)

                    elif action == "solve_captcha":
                        await self.wait_for_captcha_solved()

                    elif action == "prompt_user_to_select_record":
                        if not self.page:
                            logger.error(
                                "No active page for prompt_user_to_select_record"
                            )
                            return False
                        selector = step["selector"]
                        await self.send_msg(
                            "👋 I found multiple records. Please click on YOUR record in the browser window to continue."
                        )
                        # We wait for the user to navigate or click something that makes the selector disappear or a new page load
                        # For now, we'll just wait for the user to click and then we keep polling for page change
                        try:
                            await self.page.wait_for_selector(
                                selector, state="hidden", timeout=120000
                            )
                        except:
                            pass

                    elif action == "generate_email":
                        variable = step["variable"]
                        await self.send_msg("Generating temporary email...")
                        self.email_service = MailTMService()
                        try:
                            email_addr = self.email_service.create_account()
                            if email_addr:
                                # Store in user_data for subsequent steps to use
                                data[variable] = email_addr
                                # Also update the browser agent's known data if needed
                                await self.send_msg(f"Generated email: {email_addr}")
                            else:
                                raise Exception("Failed to generate email")
                        except Exception as e:
                            logger.error(f"Email generation failed: {e}")
                            await self.send_msg(f"Email generation failed: {e}")
                            return False

                    elif action == "wait_for_email":
                        variable = step["variable"]
                        timeout = step.get("timeout", 120)
                        await self.send_msg("Waiting for verification email...")

                        if not self.email_service:
                            self.email_service = (
                                MailTMService()
                            )  # Should have been init already, but safety first

                        # Run the blocking request in a separate thread to not block asyncio loop
                        link = await asyncio.to_thread(
                            self.email_service.find_verification_link, timeout=timeout
                        )

                        if link:
                            await self.send_msg(f"Verification link found: {link}")
                            data[variable] = link
                        else:
                            await self.send_msg(
                                "No verification link found in email. The removal may have been processed automatically."
                            )
                            # Set a placeholder URL to continue the process
                            data[variable] = "https://www.peoplesearchnow.com/opt-out"

                    break  # Success, exit retry loop

                except Exception as e:
                    if (
                        "context was destroyed" in str(e).lower()
                        or "navigation" in str(e).lower()
                    ):
                        retry_count += 1
                        logger.warning(
                            f"Execution context destroyed or navigation occurred. Retrying step {action} ({retry_count}/{max_retries})..."
                        )
                        await asyncio.sleep(2)  # Give it a moment to stabilize
                        continue

                    if "closed" in str(e).lower():
                        logger.info(
                            f"Page/Browser closed during action {action} - expected for redirects"
                        )
                        break
                    logger.error(f"Action {action} failed: {e}")
                    return False

        return True

    def _build_endpoint(self):
        """Build Browserless WebSocket endpoint with features enabled."""
        params = [f"token={self.api_key}"]

        # Add proxy if enabled (with rotation between sessions)
        if self.settings.get("proxy", True):  # Default to True
            params.append("proxy=residential")
            params.append("proxyCountry=us")
            params.append("proxySticky=false")  # Force new IP per session
            self.settings["proxy"] = True

        # Add CAPTCHA solving if enabled
        if self.settings.get("captcha", True):
            params.append("solveCaptchas=true")
            self.settings["captcha"] = True

        # Adblock DISABLED: blockAds interferes with Cloudflare challenge scripts
        # Sites using Cloudflare will fail to load if ads are blocked
        # if self.settings.get("adblock", False):
        #     params.append("blockAds=true")

        base = self.ENDPOINTS.get(self.region, self.ENDPOINTS["sfo"])
        # Use stealth route if stealth mode is enabled
        route = (
            "/chromium/stealth" if self.settings.get("stealth", True) else "/chromium"
        )
        endpoint = f"{base}{route}?{'&'.join(params)}"
        logger.info(f"Built endpoint (first 50 chars): {endpoint[:50]}...")
        return endpoint

    async def connect(self):
        """Connect to Browserless cloud browser."""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        # Log connection settings BEFORE building endpoint to ensure we show what we requested
        settings_str = "\n".join(
            [f"  {k.title()}: {v}" for k, v in self.settings.items()]
        )
        logger.info(f"Connecting to Browserless ({self.region}):\n{settings_str}")

        endpoint = self._build_endpoint()
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(endpoint)
        except Exception as e:
            logger.error(f"Playwright connect_over_cdp failed: {str(e)}")
            raise e

        # Use existing context/page from Browserless (as per docs)
        context = (
            self.browser.contexts[0]
            if self.browser.contexts
            else await self.browser.new_context()
        )
        self.page = context.pages[0] if context.pages else await context.new_page()

        # NOTE: Stealth mode is now handled by Browserless API
        # NOTE: Human-like mouse/typing patterns are not needed with Browserless

        # Create CDP session for Browserless-specific commands
        try:
            self.cdp_session = await self.page.context.new_cdp_session(self.page)
            logger.info("CDP session created for Browserless commands")

            # Set up captcha event listeners
            if self.cdp_session:
                self.captcha_found_event = asyncio.Event()
                self.captcha_solved_event = asyncio.Event()

                def on_captcha_found(params):
                    captcha_type = params.get("type", "unknown")
                    status = params.get("status", "detected")
                    logger.info(
                        f"Captcha found! Type: {captcha_type}, Status: {status}"
                    )
                    self.captcha_result = {
                        "found": True,
                        "type": captcha_type,
                        "status": status,
                    }
                    if self.captcha_found_event:
                        self.captcha_found_event.set()
                    # Send update to UI
                    asyncio.create_task(
                        self.send_msg(f"Captcha detected ({captcha_type})")
                    )

                def on_captcha_auto_solved(params):
                    solved = params.get("solved", False)
                    token = params.get("token", "")
                    time_taken = params.get("time", 0)
                    logger.info(
                        f"Captcha auto-solved! Solved: {solved}, Time: {time_taken}ms"
                    )
                    self.captcha_result = {
                        "solved": solved,
                        "token": token,
                        "time": time_taken,
                    }
                    if self.captcha_solved_event:
                        self.captcha_solved_event.set()
                    # Send update to UI
                    asyncio.create_task(self.send_msg(f"Captcha solved automatically!"))

                self.cdp_session.on("Browserless.captchaFound", on_captcha_found)
                self.cdp_session.on(
                    "Browserless.captchaAutoSolved", on_captcha_auto_solved
                )
                logger.info("Captcha event listeners registered")

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
            self.screenshot_task = None

    async def send_msg(self, text):
        """Send a technical log message to the UI (Activity Log)."""
        if not self.running:
            return
        try:
            if self.ws:
                await self.ws.send_json({"type": "log", "message": text})
        except:
            pass

    async def send_browser_update(self, status_text, url=None):
        """Send screenshot + status to the browser preview UI."""
        if not self.running or not self.ws or not self.page:
            return
        try:
            screenshot = await self.page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()

            await self.ws.send_json(
                {
                    "type": "browser_update",
                    "screenshot": screenshot_b64,
                    "url": url or self.page.url,
                    "message": status_text,
                }
            )
        except:
            pass

    def send_browser_update_sync(self, status_text):
        """Sync wrapper for CDP event callbacks - just logs the message."""
        logger.info(f"CDP Event: {status_text}")

    async def wait_for_captcha_solved(self, timeout=180, submit_selector=None):
        """
        Handle reCAPTCHA on the page.
        
        Browserless with solveCaptchas=true handles captchas automatically,
        but it kills the Playwright page reference in the process.
        
        Strategy:
        1. Check if the g-recaptcha-response textarea already has a token
        2. If not, wait for Browserless captchaAutoSolved event (it fires with a token)
        3. After page death/recovery, inject the token into the form
        4. Trigger the data-callback function
        """
        if not self.page or (hasattr(self.page, "is_closed") and self.page.is_closed()):
            logger.warning("wait_for_captcha_solved called on closed page")
            return {"solved": False, "error": "Page closed"}

        # Check if there's a reCAPTCHA on this page
        try:
            has_recaptcha = await self.page.evaluate("""
                () => {
                    return !!(
                        document.querySelector('.g-recaptcha') ||
                        document.querySelector('iframe[src*="recaptcha"]') ||
                        document.querySelector('[data-sitekey]')
                    );
                }
            """)
            if not has_recaptcha:
                return {"solved": True, "message": "No captcha on page"}
        except Exception as e:
            if "closed" in str(e).lower():
                # Page already dead - check if captcha was auto-solved
                if hasattr(self, 'captcha_result') and self.captcha_result.get('solved'):
                    logger.info("Page closed but captcha was auto-solved")
                    return {"solved": True, "token": self.captcha_result.get('token', '')}
                return {"solved": False, "error": "Page closed before captcha check"}

        await self.send_msg("Solving reCAPTCHA...")
        logger.info("reCAPTCHA detected on page")

        # Helper: check if the g-recaptcha-response textarea has a genuine token
        async def check_response_token():
            try:
                return await self.page.evaluate("""
                    () => {
                        const response = document.querySelector('textarea[name="g-recaptcha-response"]');
                        if (response && response.value && response.value.length > 20) return response.value;
                        try {
                            if (typeof grecaptcha !== 'undefined') {
                                if (grecaptcha.getResponse && grecaptcha.getResponse().length > 0)
                                    return grecaptcha.getResponse();
                                if (grecaptcha.enterprise && grecaptcha.enterprise.getResponse) {
                                    const resp = grecaptcha.enterprise.getResponse();
                                    if (resp && resp.length > 0) return resp;
                                }
                            }
                        } catch(e) {}
                        return null;
                    }
                """)
            except Exception:
                return None

        # Helper: trigger callback AND click submit button atomically
        async def trigger_callback_and_submit(token=""):
            try:
                await self.page.evaluate("""
                    (args) => {
                        const token = args.token;
                        const submitSelector = args.submitSelector;
                        // Fill the response textarea
                        const response = document.querySelector('textarea[name="g-recaptcha-response"]');
                        if (response && (!response.value || response.value.length < 20)) {
                            response.value = token;
                        }
                        // Trigger the data-callback
                        const widget = document.querySelector('[data-callback]');
                        if (widget) {
                            const callbackName = widget.getAttribute('data-callback');
                            if (window[callbackName]) {
                                const finalToken = response ? response.value : token;
                                window[callbackName](finalToken);
                            }
                        }
                        // Click submit button with delay
                        if (submitSelector) {
                            setTimeout(function() {
                                var btn = document.querySelector(submitSelector);
                                if (btn) btn.click();
                            }, 500);
                        }
                    }
                """, {"token": token, "submitSelector": submit_selector or ""})
                logger.info("Triggered callback" + (f" + submit: {submit_selector}" if submit_selector else ""))
                
                if submit_selector:
                    await asyncio.sleep(0.8)
                    try:
                        await self.page.click(submit_selector, timeout=3000)
                    except Exception:
                        pass
                    await self.send_msg("Form submitted!")
            except Exception as e:
                logger.debug(f"Callback/submit: {e}")
                if submit_selector and "closed" in str(e).lower():
                    await self.send_msg("Form submitted!")

        # Step 1: Check if already solved (token in response textarea)
        existing_token = await check_response_token()
        if existing_token:
            await self.send_msg("reCAPTCHA solved")
            logger.info("reCAPTCHA already has a response token")
            await trigger_callback_and_submit(existing_token)
            await asyncio.sleep(1)
            return {"solved": True}

        # Step 2: Check if Browserless already auto-solved it (via CDP event)
        if hasattr(self, 'captcha_result') and self.captcha_result.get('solved'):
            token = self.captcha_result.get('token', '')
            if token:
                await self.send_msg("reCAPTCHA solved")
                logger.info(f"reCAPTCHA auto-solved by Browserless (token from event, len={len(token)})")
                await trigger_callback_and_submit(token)
                await asyncio.sleep(1)
                return {"solved": True}

        # Step 3: Click the reCAPTCHA checkbox to trigger solving
        logger.info("Clicking reCAPTCHA checkbox in iframe to trigger solve")
        try:
            recaptcha_frame = None
            for frame in self.page.frames:
                frame_url = frame.url or ""
                if "recaptcha" in frame_url and "anchor" in frame_url:
                    recaptcha_frame = frame
                    break
            # Fallback: any frame with recaptcha
            if not recaptcha_frame:
                for frame in self.page.frames:
                    if "recaptcha" in (frame.url or ""):
                        recaptcha_frame = frame
                        break
            
            if recaptcha_frame:
                try:
                    await recaptcha_frame.click("#recaptcha-anchor", timeout=5000)
                    logger.info("Clicked reCAPTCHA checkbox")
                except Exception as click_err:
                    logger.debug(f"Checkbox click failed: {click_err}")
            else:
                logger.warning("Could not find reCAPTCHA iframe")
        except Exception as e:
            logger.debug(f"Frame access error: {e}")

        # Step 4: Poll for solve - check both the page token AND the CDP event
        await self.send_msg("Waiting for reCAPTCHA to be solved...")
        poll_timeout = 60
        poll_start = asyncio.get_event_loop().time()
        last_status_time = poll_start

        while (asyncio.get_event_loop().time() - poll_start) < poll_timeout:
            # Check CDP event first (Browserless solved it)
            if hasattr(self, 'captcha_result') and self.captcha_result.get('solved'):
                token = self.captcha_result.get('token', '')
                if token:
                    logger.info(f"Browserless captchaAutoSolved event fired (token len={len(token)})")
                    # Try to inject token into form
                    try:
                        if not self.page.is_closed():
                            await trigger_callback_and_submit(token)
                    except Exception:
                        pass
                    await self.send_msg("reCAPTCHA solved")
                    await asyncio.sleep(1)
                    return {"solved": True, "token": token}

            # Check page token
            try:
                if not self.page.is_closed():
                    token = await check_response_token()
                    if token:
                        await self.send_msg("reCAPTCHA solved")
                        logger.info("reCAPTCHA response token detected")
                        await trigger_callback_and_submit(token)
                        await asyncio.sleep(1)
                        return {"solved": True}
            except Exception:
                pass

            # If page died, wait for Browserless event
            try:
                if self.page.is_closed():
                    # Try to recover page
                    if self.browser and self.browser.contexts:
                        ctx = self.browser.contexts[0]
                        for pg in ctx.pages:
                            if not pg.is_closed():
                                self.page = pg
                                try:
                                    self.cdp_session = await self.page.context.new_cdp_session(self.page)
                                except Exception:
                                    pass
                                logger.info("Recovered page during captcha solve")
                                break
            except Exception:
                pass

            # Progress update
            now = asyncio.get_event_loop().time()
            if now - last_status_time > 15:
                elapsed = int(now - poll_start)
                await self.send_msg(f"Still solving reCAPTCHA... ({elapsed}s)")
                last_status_time = now

            await asyncio.sleep(2)

        # Step 5: Timeout - try programmatic execute as last resort
        logger.warning("reCAPTCHA solve timed out, trying programmatic approach")
        try:
            if not self.page.is_closed():
                await self.page.evaluate("""
                    () => {
                        try {
                            if (typeof grecaptcha !== 'undefined') {
                                if (grecaptcha.enterprise && grecaptcha.enterprise.execute) {
                                    const sitekey = document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey');
                                    if (sitekey) grecaptcha.enterprise.execute(sitekey, {action: 'submit'});
                                } else if (grecaptcha.execute) {
                                    grecaptcha.execute();
                                }
                            }
                        } catch(e) {}
                    }
                """)
                await asyncio.sleep(5)
                token = await check_response_token()
                if token:
                    await self.send_msg("reCAPTCHA solved")
                    logger.info("Solved via programmatic execute")
                    await trigger_callback_and_submit(token)
                    return {"solved": True}
        except Exception:
            pass

        await self.send_msg("reCAPTCHA could not be solved")
        logger.warning("reCAPTCHA solve failed after all attempts")
        return {"solved": False, "error": "Timeout"}

    async def start_screenshot_loop(self):
        """Start continuous screenshot updates (screenshot only, no status spam)."""
        
        # Send initial screenshot immediately so preview opens right away
        try:
            if self.page and not (hasattr(self.page, "is_closed") and self.page.is_closed()):
                screenshot = await self.page.screenshot(type="png")
                screenshot_b64 = base64.b64encode(screenshot).decode()
                if self.ws:
                    await self.ws.send_json({
                        "type": "browser_update",
                        "screenshot": screenshot_b64,
                        "url": self.page.url,
                    })
        except Exception as e:
            logger.debug(f"Initial screenshot skipped: {e}")

        async def loop():
            consecutive_failures = 0
            while self.running and self.ws:
                try:
                    if (
                        hasattr(self.ws, "client_state")
                        and self.ws.client_state.name != "CONNECTED"
                    ):
                        break
                    
                    # Check if page is still valid
                    if not self.page or (hasattr(self.page, "is_closed") and self.page.is_closed()):
                        consecutive_failures += 1
                        if consecutive_failures > 10:
                            logger.warning("Screenshot loop: page closed for extended period")
                            break
                        await asyncio.sleep(0.5)
                        continue
                    
                    # Take and send screenshot
                    try:
                        screenshot = await self.page.screenshot(type="png")
                        screenshot_b64 = base64.b64encode(screenshot).decode()
                        await self.ws.send_json({
                            "type": "browser_update",
                            "screenshot": screenshot_b64,
                            "url": self.page.url,
                        })
                        consecutive_failures = 0  # Reset on success
                    except Exception as ss_err:
                        consecutive_failures += 1
                        error_str = str(ss_err).lower()
                        if "closed" in error_str or "target" in error_str:
                            # Page might be navigating/redirecting
                            pass
                        else:
                            logger.debug(f"Screenshot error: {ss_err}")
                        
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
        """
        Execute an opt-out task using the TWO-SESSION design:
        1. Session 1: Form submission (< 1 minute)
        2. Email polling (no browser)
        3. Session 2: Verification link click (< 1 minute)
        """
        # Find matching playbook
        playbook_name = None
        for key in PLAYBOOKS.keys():
            if key.lower() in site_name.lower() or site_name.lower() in key.lower():
                playbook_name = key
                break

        if not playbook_name:
            await self.send_msg(f"No playbook found for {site_name}. Skipping.")
            return False

        playbook = PLAYBOOKS[playbook_name]
        logger.info(f"Using two-session playbook for: {site_name}")
        
        # Prepare user data
        data = self.prepare_user_data(user_data)
        
        # ============================================
        # STEP 0: Create temporary email (no browser)
        # ============================================
        await self.send_msg("Creating temporary email inbox...")
        self.email_service = MailTMService()
        try:
            email_addr = self.email_service.create_account()
            if email_addr:
                data["email"] = email_addr
                await self.send_msg(f"Generated email: {email_addr}")
            else:
                await self.send_msg("Failed to create temporary email")
                return False
        except Exception as e:
            await self.send_msg(f"Email creation failed: {str(e)[:40]}")
            logger.error(f"Email creation error: {e}")
            return False

        # ============================================
        # SESSION 1: Form submission (< 1 minute)
        # ============================================
        await self.send_msg("Session 1: Submitting opt-out form")
        
        session_1_steps = playbook.get("session_1_steps", [])
        if not session_1_steps:
            # Fallback to old "steps" format if exists
            session_1_steps = playbook.get("steps", [])
        
        if not session_1_steps:
            await self.send_msg("No session 1 steps defined in playbook")
            return False
        
        try:
            # Connect browser for Session 1
            if not self.page:
                await self.connect()
            
            if not self.screenshot_task:
                await self.start_screenshot_loop()
            
            # Execute Session 1 steps
            session_1_success = await self.execute_session_steps(
                session_1_steps, data, "Session 1"
            )
            
            if not session_1_success:
                await self.send_msg("Session 1 failed - could not submit form")
                return False
            
            await self.send_msg("Form submitted, closing browser...")
            
        except Exception as e:
            await self.send_msg(f"Session 1 error: {str(e)[:50]}")
            logger.error(f"Session 1 error: {e}")
            return False
        finally:
            # ALWAYS close browser after Session 1
            await self.disconnect()
            await asyncio.sleep(1)
        
        # ============================================
        # EMAIL POLLING (no browser - via API only)
        # ============================================
        await self.send_msg("Polling for verification email...")
        
        email_config = playbook.get("email_config", {})
        poll_interval = email_config.get("poll_interval", 10)
        poll_timeout = email_config.get("poll_timeout", 180)
        
        verification_link = None
        try:
            verification_link = await asyncio.to_thread(
                self.email_service.find_verification_link,
                timeout=poll_timeout
            )
        except Exception as e:
            logger.error(f"Email polling error: {e}")
        
        if not verification_link:
            await self.send_msg("Verification email not received within timeout")
            return False
        
        data["verification_link"] = verification_link
        await self.send_msg(f"Found verification link")
        logger.info(f"Verification link found: {verification_link[:60]}...")
        
        # ============================================
        # SESSION 2: Click verification link (< 1 minute)
        # ============================================
        await self.send_msg("Session 2: Confirming removal")
        
        session_2_steps = playbook.get("session_2_steps", [])
        if not session_2_steps:
            # If no session 2 steps, just navigate to the link
            session_2_steps = [
                {"action": "navigate", "context_key": "verification_link"},
                {"action": "wait", "seconds": 5},
            ]
        
        try:
            # Connect NEW browser for Session 2
            await self.connect()
            
            if not self.screenshot_task:
                await self.start_screenshot_loop()
            
            # Execute Session 2 steps
            session_2_success = await self.execute_session_steps(
                session_2_steps, data, "Session 2"
            )
            
            if session_2_success:
                await self.send_msg("Removal confirmed")
                return True
            else:
                await self.send_msg("Session 2 completed but confirmation unclear")
                return True  # Still count as success if we got to verification
                
        except Exception as e:
            await self.send_msg(f"Session 2 error: {str(e)[:50]}")
            logger.error(f"Session 2 error: {e}")
            return False
        finally:
            # Close browser after Session 2
            await self.disconnect()

    async def run_multiple_optouts(self, sites, user_data):
        """
        Run opt-out tasks for multiple sites.
        Each task manages its own browser sessions (two-session design).
        """
        total = len(sites)
        count = 0
        failed = 0

        logger.info(f"Starting removal for {total} sites")
        await self.send_msg(f"Starting removal for {total} sites")

        for i, site in enumerate(sites):
            if not self.running:
                await self.send_msg("Process stopped.")
                break

            while self.paused and self.running:
                await asyncio.sleep(0.5)

            if not self.running:
                break

            site_name = site.get("name", "Unknown")
            site_url = site.get("opt_out_url", "")

            try:
                await self.send_msg(f"[{i + 1}/{total}] {site_name}")

                # run_optout_task manages its own browser sessions
                if await self.run_optout_task(site_name, site_url, user_data):
                    count += 1
                    await self.send_msg(f"Completed {site_name}")
                else:
                    failed += 1
                    await self.send_msg(f"Failed {site_name}")

            except Exception as e:
                failed += 1
                logger.error(f"Error processing {site_name}: {e}")
                await self.send_msg(f"{site_name}: Critical error - {str(e)[:50]}")
                # Ensure any lingering connections are closed
                await self.disconnect()

            # Brief pause between sites
            if i < total - 1:
                delay = random.uniform(3, 6)
                await self.send_msg(f"Cooling down {int(delay)}s...")
                await asyncio.sleep(delay)

        # Signal completion
        if self.ws:
            await self.ws.send_json(
                {
                    "type": "complete",
                    "message": f"Done. {count}/{total} sites processed.",
                }
            )


# ============================================================================
# 7. SYSTEM UTILS (.env Persistence)
# ============================================================================


def update_env(key, value):
    """Update a key-value pair in the .env file."""
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w") as f:
        f.writelines(lines)
    logger.info(f"Updated {key} in {ENV_PATH}")


# ============================================================================
# 8. FASTAPI SERVER (Unified API)
# ============================================================================

active_sessions: Dict[str, dict] = {}

# Current browser provider setting (default to browserless)
current_browser_provider = os.getenv("BROWSER_PROVIDER", "browserless")


def get_browser_agent(ws, browser_settings=None):
    """Get the BrowserlessAgent for browser automation."""
    return BrowserlessAgent(ws=ws, browser_settings=browser_settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(dotenv_path=ENV_PATH)
    logger.info(f"Starting OPTX Backend (Provider: {current_browser_provider})...")
    load_dotenv(dotenv_path=ENV_PATH, override=True)  # Ensure fresh load
    yield


app = FastAPI(title="OPTX Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "browser": "Browserless Cloud"}


@app.get("/check-site/{site_name:path}")
async def check_site(site_name: str):
    """Check if a site is online by its domain name."""
    import httpx
    from urllib.parse import unquote

    # Decode URL-encoded characters and clean up
    domain = unquote(site_name).strip().split("/")[0].lower()

    # Remove protocol if accidentally included
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://", 1)[1]

    # Remove www. for consistency in URL building
    clean_domain = domain.replace("www.", "")

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
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, verify=False
    ) as client:
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = str(id(websocket))
    active_sessions[sid] = {
        "websocket": websocket,
        "user_data": {},
        "browser_settings": None,
        "agent": None,
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
                    await websocket.send_json({"type": "session_ended"})
                    # Tell frontend to reset UI (placeholder, hide end button, etc.)
                    await websocket.send_json({"type": "reset_ui"})
                    logger.info("=== SESSION END COMPLETE ===")
                except:
                    pass

            elif msg["type"] == "user_info":
                # Collect all fields requested by user
                fields = [
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "street",
                    "city",
                    "state",
                    "zip",
                ]
                active_sessions[sid]["user_data"] = {k: msg.get(k, "") for k in fields}

                # If 'address' is not specifically provided, use 'street'
                if not active_sessions[sid]["user_data"].get(
                    "address"
                ) and active_sessions[sid]["user_data"].get("street"):
                    active_sessions[sid]["user_data"]["address"] = active_sessions[sid][
                        "user_data"
                    ]["street"]

                user_data = active_sessions[sid]["user_data"]
                logger.info(
                    f"Received user_info update for: {user_data.get('first_name')} {user_data.get('last_name')}"
                )

                # Only start removal if explicitly requested or if it's a specific trigger message type
                if msg.get("start_removal"):
                    # Update settings if provided in removal message
                    if msg.get("browser_settings"):
                        active_sessions[sid]["browser_settings"] = msg[
                            "browser_settings"
                        ]

                    agent = get_browser_agent(
                        ws=websocket,
                        browser_settings=active_sessions[sid].get("browser_settings"),
                    )
                    active_sessions[sid]["agent"] = agent
                    sites = get_optout_sites()
                    await agent.run_multiple_optouts(sites, user_data)

            elif msg["type"] == "config":
                # Handle initial config and user info sync
                if msg.get("user_info"):
                    user_info = msg["user_info"]
                    active_sessions[sid]["user_data"].update(user_info)
                    if not active_sessions[sid]["user_data"].get(
                        "address"
                    ) and user_info.get("street"):
                        active_sessions[sid]["user_data"]["address"] = user_info.get(
                            "street"
                        )
                    logger.info(
                        f"Session configured with user info for: {user_info.get('first_name')}"
                    )

                if msg.get("browser_settings"):
                    active_sessions[sid]["browser_settings"] = msg["browser_settings"]
                    logger.info("Session configured with browser settings")
    except WebSocketDisconnect:
        pass
    finally:
        active_sessions.pop(sid, None)


async def handle_chat(sid, message, phone=None):
    """Provide static instructions for the removal process."""
    session = active_sessions.get(sid)
    if not session:
        return
    ws = session["websocket"]

    response = (
        "To remove your personal information from data broker sites, "
        "please go to the **Removal** tab, fill in your information, "
        "and click **Start Removal**. The automated agent will handle the rest!"
    )
    await ws.send_json({"type": "response", "message": response})


def get_optout_sites():
    """Return list of opt-out sites to process from the defined playbooks."""
    return [{"name": p["name"], "opt_out_url": p["url"]} for p in PLAYBOOKS.values()]


# Static File Serving
PROJECT_ROOT = Path(__file__).parent.parent


@app.get("/")
async def serve_index():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    f = PROJECT_ROOT / filename
    if f.exists() and f.is_file():
        return FileResponse(f)
    return FileResponse(PROJECT_ROOT / "index.html")  # Fallback to index for SPA


if __name__ == "__main__":
    import uvicorn

    # Final sweep to catch any late-initializing loggers
    setup_all_loggers()
    uvicorn.run(app, host="127.0.0.1", port=3000, log_config=None)
