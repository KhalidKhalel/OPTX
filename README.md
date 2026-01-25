<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com/?lines=OPTX+-+Online+Privacy+Tool+eXtractor;Fully+Agentic+Mode;Protect+Your+Privacy+Online;Know+Where+Your+Data+Lives;Remove+Your+Digital+Footprint;Learn+to+Limit+Your+Online+Exposure;Made+by+Khalid+Khalel&font=Fira%20Code&center=true&width=700&height=50&color=8B5CF6&vCenter=true&pause=3000&size=24&background=1A1B27&duration=4000" />
  </a>
</p>

<br/>

<p align="center">
  <a href="#" title="Live Website - Coming Soon">
    <img src="https://img.shields.io/badge/🌐_Live_Website-Coming_Soon-01FFFF?style=for-the-badge&labelColor=1A1B27" alt="Live Website - Coming Soon"/>
  </a>
</p>

<p align="center">
  <a href="https://www.khalidkhalel.com/" title="Website"><img width="32px" alt="Website" src="https://img.icons8.com/ios/50/8B5CF6/internet.png"/></a>
  &#8287;&#8287;&#8287;&#8287;&#8287;
  <a href="https://linkedin.com/in/khalidkhalel" title="LinkedIn"><img width="32px" alt="LinkedIn" src="https://img.icons8.com/ios/50/8B5CF6/linkedin.png"/></a>
  &#8287;&#8287;&#8287;&#8287;&#8287;
  <a href="mailto:contact.khalidk@gmail.com" title="Email"><img width="32px" alt="Email" src="https://img.icons8.com/ios/50/8B5CF6/mail.png"/></a>
</p>

<br/>

---

## 🎯 What is OPTX?

**OPTX** (Online Privacy Tool eXtractor) is an Open Source Intelligence (OSINT) assistant designed to help users understand and manage their digital footprint. By providing transparent access to public telecom and data broker information, users can see exactly what information is publicly available about them.

### 🔍 People Search Sites

OPTX specifically targets **people search sites** — data brokers that trade personal information for profit. These sites collect and expose names, addresses, phone numbers, relatives, and more.

**Why this matters:** Exposed personal data puts you at risk of:
- Unwanted marketing and spam
- Identity theft and financial hacks
- Account takeovers
- Robocalls and phone scams
- Stalking, harassment, and doxing

> [!NOTE]
> OPTX does **not** target employment verification sites or employer background check services — only people search sites that expose your personal info publicly.

| Feature | Description |
|---------|-------------|
| 🔍 **Phone Lookup** | Search **40+** people-search sites instantly (more added daily) |
| 📊 **Carrier Info** | Live carrier & rate center data from public telecom records |
| 🧠 **Agent Mode** | **Truly Agentic**: AI "thinks" & navigates sites dynamically like a human |
| 📺 **Live Preview** | Watch the AI reason and act in real-time through the browser window |
| 🔐 **CAPTCHA Solver** | Intelligent handling of bot-checks using vision and audio |
| 💬 **AI Assistant** | Learn about data exposure, proactive protection strategies, and initiate intelligent, automatic removals through natural conversation. |

---

## 🧠 How the Agent "Thinks"

OPTX isn't just a script—it's a **smart agent** that uses AI to navigate websites like a human would. Here's how it works:

### The Observer-Actor Loop

The agent doesn't follow a static list of commands. Instead, it runs a continuous loop:

1. **Observe**: "Look" at the page by getting the DOM (the structural map) and taking a screenshot.
2. **Reason**: An AI vision model analyzes the page. It recognizes things like "that looks like a search bar" or "this button starts the removal process."
3. **Act**: Based on reasoning, it decides the next step (click a link, fill a field, solve a CAPTCHA).
4. **Verify**: After acting, it checks the result. If something unexpected happens (like a popup), it adjusts on the fly.

### Semantic Understanding

The agent understands **intent**, not just code. If a site changes its button from "Delete" to "Remove my data," a normal script would break. But because the AI can "read" text and understand context, it knows both mean the same thing.

### Vision & Structure

The agent combines **visual layout** (what a person sees) with **structural data** (the DOM code). This allows it to navigate menus, handle CAPTCHAs, and steer through "dark patterns" (the tricky ways sites hide their opt-out forms).

---

## 🏗️ Architecture: What Runs Where

| Capability | How It Works |
|------------|--------------|
| ✅ **Observer-Actor Loop** | Your code observes (screenshots, DOM) and acts (click, fill). The *reasoning* is handled by Browser-Use API. |
| ✅ **Semantic Understanding** | Provided by Browser-Use API via the vision model. It understands intent, not just exact selectors. |
| ✅ **Vision & Structure** | Browser-Use combines vision (seeing the page) with DOM structure (reading the code). |
| ❌ **Sub-Agents for Research** | Not included. OPTX runs one task at a time (perfect for opt-outs). |

### Code Distribution

| Part | Where it runs |
|------|---------------|
| Browser control (Playwright) | **Your code** (local) |
| Site-specific opt-out logic | **Your code** (local) |
| Chatbot persona | Cerebras **API** (cloud) |
| Smart reasoning / vision | Browser-Use **API** (cloud) |

### What's in `agent.py`:
- **Automation logic**: Navigating to URLs, filling forms, clicking buttons, taking screenshots.
- **Site-specific handlers**: Custom flows for Nuwber, 411.info, ThatsThem, etc.
- **Chatbot persona**: How the bot talks to users (powered by Cerebras API).

### What's handled by Browser-Use API:
- **Reasoning**: When the agent needs to figure out *which* button to click, that intelligence is provided by Browser-Use's cloud model (`browser-use-llm`).
- **Vision**: It can "see" screenshots and understand what's on the page.
- **Decision-making**: It decides the next action based on visual and structural data.

---

## 🔒 Privacy & Data Protection

### How Your Personal Info is Protected

OPTX uses Browser-Use's **`sensitive_data`** feature to protect your personal information during automated opt-outs.

| Your Data | Where It's Stored | Sent to AI? |
|-----------|-------------------|-------------|
| **Name, Address, Phone, DOB** | Local browser only | ❌ **No** - AI sees placeholders like `{first_name}` |
| **API Keys** | `.env` file (local) | ❌ **No** - Never leaves your machine |
| **Chat Messages** | Sent to Cerebras | ⚠️ **Yes** - Required for AI responses |
| **Browser Screenshots** | Sent to Browser-Use | ⚠️ **Yes** - AI needs to "see" pages |

### How `sensitive_data` Works

When you enter your personal info in Settings → Your Info, it's stored **locally** in your browser. During opt-outs, the AI only sees placeholders:

```
AI sees: "Fill form with {first_name} {last_name} at {street}, {city} {state}"
AI never sees: "Fill form with John Doe at 123 Main St, Austin TX"
```

The actual values are filled in **locally** by the browser automation, not by the AI.

> [!IMPORTANT]
> **AI Context & Protection**:
> - **Conversational Awareness**: Your information (Name, Email, Phone, Address, etc.) is used to enrich the AI chatbot's context. This allows it to acknowledge who you are and what data it's helping you protect (e.g., "I see your email is example@test.com, let's look for that on Nuwber").
> - **Form Filling**: For actual automation, data is protected via `sensitive_data` placeholders (e.g., `{email}`) so the browser automation filling the forms knows the value, but the AI vision model only sees the placeholder tag.
> 
> **Local Mode**: 100% private. Nothing leaves your machine.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/KhalidKhalel/OPTX.git
```

```bash
cd OPTX
```

### 2. Install & Run

```bash
# Verify environment & start server
make
```

> [!NOTE]
> The `make` command handles everything: it creates a virtual environment, installs dependencies, and starts the server on [http://localhost:3000](http://localhost:3000).

---

### 3. Install Make (if needed)

If you get `make: command not found`, follow the instructions for your operating system:

---

##  macOS

**Option 1: Xcode Command Line Tools** (Recommended)

```bash
xcode-select --install
```

A popup will appear - click "Install" and wait for it to complete.

**Option 2: Using Homebrew**

```bash
brew install make
```

---

## ⊞ Windows

**Option 1: Git Bash** (Easiest - Recommended)

If you have Git installed, you already have Git Bash!

1. Open VS Code
2. Open the terminal (`` Ctrl+` `` or View → Terminal)
3. Click the dropdown arrow next to the `+` button in the terminal
4. Select **"Git Bash"**
5. Set it as default: Click dropdown → "Select Default Profile" → "Git Bash"

Done! Now you can run all `make` commands.

**Option 2: Install Make with Chocolatey**

1. Open PowerShell as **Administrator** (right-click → "Run as Administrator")

2. Install Chocolatey:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

3. Close and reopen PowerShell as Administrator

4. Install Make:

```powershell
choco install make
```

5. **Important:** Restart VS Code completely for the changes to take effect

---

### ✅ Verify Make Installation

```bash
make --version
```

---

## 🎮 How It Works

### 1️⃣ Search
Enter a phone number → OPTX checks **40+** data broker sites (new ones added daily).

### 2️⃣ Review
See which sites have your info with direct links to their opt-out forms.

### 3️⃣ Remove (True Agent Mode)
- **Manual:** Click the links and follow the steps yourself.
- **Intelligent Agent:** The bot doesn't follow a script; it dynamically observes the page, reasons about where to click, fills forms, and solves puzzles just like a human—meaning every run is unique. You can watch the whole process live in the **Browser Preview**.

---

## ⚙️ Commands

| Command | Description |
|---------|-------------|
| `make` | Install dependencies & start server at localhost:3000 |
| `make update` | Pull latest changes and update dependencies |
| `make stop` | Stop the server |
| `make clean` | Remove venv and cache |

---

## 🛠️ Built With

| Technology | Purpose | Icon |
|------------|---------|------|
| **Python** | Backend server, LLM integration, browser automation | <a href="https://www.python.org"><img src="https://skillicons.dev/icons?i=python&theme=dark" width="30"/></a> |
| **JavaScript** | Frontend logic, chat interface, dynamic UI | <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://skillicons.dev/icons?i=js&theme=dark" width="30"/></a> |
| **HTML5** | Page structure and semantic markup | <a href="https://www.w3.org/html/"><img src="https://skillicons.dev/icons?i=html&theme=dark" width="30"/></a> |
| **CSS3** | Cyberpunk styling, animations, glitch effects | <a href="https://www.w3schools.com/css/"><img src="https://skillicons.dev/icons?i=css&theme=dark" width="30"/></a> |
| **FastAPI** | REST API endpoints, WebSocket server | <a href="https://fastapi.tiangolo.com"><img src="https://skillicons.dev/icons?i=fastapi&theme=dark" width="30"/></a> |

---

## 📁 Project Structure

OPTX is a **Single Page Application (SPA)** - all views are in one HTML file with JavaScript routing.

```
OPTX/
├── index.html          # Main SPA - all views (search, protect, sources, about)
├── style.css           # Dark cyberpunk theme with glitch effects and animations
├── script.js           # Chat interface, WebSocket connection, settings management
├── sites.js            # Database of 40+ data broker sites with opt-out URLs
├── .env                # Your API keys (not committed to git)
├── Makefile            # Easy commands: make, update, clean
└── backend/
    ├── agent.py        # Main server: LLM chat, browser automation, CAPTCHA solving
    └── phone_lookup.py # Phone carrier and rate center lookups
```

---

## 🔐 Environment Setup

Create `.env` in the project root:

```env
# Chatbot - Cerebras (SUPER FAST, FREE)
# Get your key at: https://cloud.cerebras.ai
CEREBRAS_API_KEY=csk-your-key
CHATBOT_MODEL=zai-glm-4.7

# Browser Automation - Browser-Use (FREE, handles forms automatically)
# Get your key at: https://cloud.browser-use.com
BROWSER_USE_API_KEY=bu_your-key
VISION_MODEL=browser-use-llm

# Cloud Browser - Browserless (FREE, CAPTCHA solving)
# Get your key at: https://browserless.io
BROWSERLESS_API_KEY=your-key
BROWSERLESS_TOKEN=your-key
BROWSERLESS_WS_URL=wss://production-sfo.browserless.io

# CAPTCHA Solver (Audio) - Optional but useful for complex bots
WIT_AI_SERVER_TOKEN=your-token
```

### 🔑 Getting Your API Keys

**1. Cerebras (Brain) - 100% FREE**
- Uses **zai-glm-4.7** at incredible speeds via Cerebras.
- Sign up at [cloud.cerebras.ai](https://cloud.cerebras.ai).

**2. Browser-Use (Eyes & Hands) - FREE Tier**
- Advanced reasoning engine that sees the page like you do.
- Get free monthly steps at [cloud.browser-use.com](https://cloud.browser-use.com).

**3. Browserless (The Browser) - FREE Tier**
- Full-featured cloud browser with anti-detection and CAPTCHA solving.
- Sign up at [browserless.io](https://www.browserless.io).
- **Stealth & CAPTCHA**: Provides comprehensive handling through both passive detection and programmatic solving. Many CAPTCHAs are prevented altogether by using the `/stealth` route, which hides signs of automation using advanced anti-detection techniques.

**4. CAPTCHA Solver (Audio) - 100% FREE**
- Optional but recommended for audio-based reCAPTCHA solving.
- [Wit.ai](https://wit.ai) | [GitHub](https://github.com/dessant/buster) | [Buster Config Guide](https://github.com/dessant/buster/wiki/Configuring-Buster-for-Wit.ai)

### 🗑️ Account Deletion (Your Rights)

If you wish to close your accounts and delete your data from the services used by OPTX, you can do so by contacting their respective support teams as per their privacy policies:

*   **Cerebras (Brain)**: Email `privacy@cerebras.ai` to request deletion of your `cloud.cerebras.ai` account. [Privacy Policy](https://www.cerebras.ai/privacy-policy)
*   **Browserless (The Browser)**: Email `support@browserless.io` to request account closure and data deletion. [Privacy Policy](https://www.browserless.io/privacy-policy)
*   **Browser-Use (Eyes & Hands)**: Email `support@browser-use.com` to request permanent account deletion. [Privacy Policy](https://browser-use.com/privacy)

> [!TIP]
> **Why is it free?** OPTX leverages the generous free tiers of best-in-class privacy and AI infrastructure. You get professional-grade removal tools without a monthly subscription.

---

## 📄 License

MIT License - Free to use, modify, and share!

---

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=Made%20by%20Khalid%20Khalel&font=Fira%20Code&center=true&width=300&height=30&color=8B5CF6&vCenter=true&pause=100000&size=18&duration=1" />
</p>
