<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com/?lines=OPTX+-+Online+Privacy+Tool+eXtractor;Protect+Your+Privacy+Online;Know+Where+Your+Data+Lives;Remove+Your+Digital+Footprint;Learn+to+Limit+Your+Online+Exposure;Made+by+Khalid+Khalel&font=Fira%20Code&center=true&width=700&height=50&color=8B5CF6&vCenter=true&pause=3000&size=24&background=1A1B27&duration=4000" />
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

### What OPTX Does

| Feature | Description |
|---------|-------------|
| 🔍 **Phone Lookup** | Search 25+ people-search sites instantly *(more sites actively being added)* |
| 📊 **Carrier Info** | Live carrier & rate center data from public telecom records |
| 🤖 **AI Automation** | AI handles opt-out forms automatically, completely free `BETA` |
| 🔐 **CAPTCHA Solver** | Audio CAPTCHA solving via Google Speech + wit.ai |
| 💬 **Chat Assistant** | OPTX Assistant guides you through the removal process |

> [!NOTE]
> **AI Automation (BETA):** This feature is not fully functional yet and can make errors. Still under active development.

---

## 🔒 Privacy

> [!NOTE]
> **API Mode**: Your chat messages are processed by OpenRouter's AI. Your personal data (name, address) for opt-outs stays local and is only used by the browser automation.
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
# Install dependencies
make install

# Start OPTX server
make run

# Open http://localhost:3000
```

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

## 🏃 Quick Start

```bash
# 1. Install dependencies
make install

# 2. Start OPTX server
make run

# 3. Open http://localhost:3000
```

---

## 🎮 How It Works

### 1️⃣ Search
Enter a phone number → OPTX checks 25+ data broker sites *(more sites actively being added)*

### 2️⃣ Review
See which sites have your info with direct opt-out links

### 3️⃣ Remove
- **Manual:** Click opt-out links and follow the steps yourself
- **Auto:** AI does it automatically, completely free `BETA`

---

## ⚙️ Commands

| Command | Description |
|---------|-------------|
| `make install` | Install Python dependencies |
| `make run` | Start server at localhost:3000 |
| `make stop` | Stop the server |
| `make update` | Pull latest changes and update dependencies |
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

```
OPTX/
├── index.html          # Home page - phone lookup, AI chat, browser view, settings
├── style.css           # Dark cyberpunk theme with glitch effects and animations
├── script.js           # Chat interface, WebSocket connection, settings management
├── sites.js            # Database of 30+ data broker sites with opt-out URLs
├── about.html          # About OPTX - mission and features overview
├── sources.html        # Data sources and attribution credits
├── .env                # Your API keys (not committed to git)
├── Makefile            # Easy commands: install, run, stop, clean, update
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
CHATBOT_MODEL=llama-3.3-70b

# Browser Automation - Browser-Use (FREE, handles forms automatically)
# Get your key at: https://cloud.browser-use.com
BROWSER_USE_API_KEY=bu_your-key
LLM_MODEL=browser-use-llm

# Cloud Browser - Browserless (FREE, CAPTCHA solving)
# Get your key at: https://browserless.io
BROWSERLESS_API_KEY=your-key
BROWSERLESS_TOKEN=your-key
BROWSERLESS_WS_URL=wss://production-sfo.browserless.io

# CAPTCHA Solver backup (optional)
WIT_AI_SERVER_TOKEN=your-token
```

### 🔑 Getting Your API Keys

**1. Cerebras (for AI Chat) - FREE**
- Go to [cloud.cerebras.ai](https://cloud.cerebras.ai)
- Sign up and create an API key
- Uses Llama 3.3 70B at ~2100 tokens/sec (super fast!)

**2. Browser-Use (for Browser Automation) - FREE**
- Go to [cloud.browser-use.com](https://cloud.browser-use.com)
- Get 1000 free steps to start
- Handles form filling with vision AI

**3. Browserless (for Cloud Browser + CAPTCHA) - FREE**
- Go to [browserless.io](https://www.browserless.io)
- Sign up for free (no credit card required)
- **Free tier includes:** 1k units/month, auto CAPTCHA solving

**4. wit.ai (for Backup CAPTCHA Solving - Optional)**
- Follow this guide: [Configuring wit.ai](https://github.com/dessant/buster/wiki/Configuring-Wit.ai)
- Only needed as backup if Browserless CAPTCHA solving fails

### 🌐 Browser Provider & Settings

OPTX uses **Browserless** for cloud browser automation. Configure in Settings > Browser:

#### Browserless Features
Full-featured cloud browser with these **free features**:

| Feature | Description |
|---------|-------------|
| **Stealth Mode** | Anti-detection & fingerprint randomization |
| **Auto CAPTCHA** | Automatically solve CAPTCHAs |
| **Residential Proxy** | Route through residential IPs (uses more units) |
| **Human-like Mode** | Smooth mouse & typing patterns |
| **Adblock** | Block ads for faster page loads |

### 🗑️ Account Deletion

If you want to delete your Browserless account:

- Email [support@browserless.io](mailto:support@browserless.io) with an account deletion request

> [!NOTE]
> I am NOT sponsored by Browserless. For OPTX to work at its best, this is the best free option available.

---

## 📄 License

MIT License - Free to use, modify, and share!

---

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=Made%20by%20Khalid%20Khalel&font=Fira%20Code&center=true&width=300&height=30&color=8B5CF6&vCenter=true&pause=100000&size=18&duration=1" />
</p>
