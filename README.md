<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com/?lines=OPTX+-+Online+Privacy+Tool+eXtractor;%F0%9F%9A%A7+Coming+Soon;Protect+Your+Privacy+Online;Know+Where+Your+Data+Lives;Remove+Your+Digital+Footprint;Learn+to+Limit+Your+Online+Exposure;Made+by+Khalid+Khalel&font=Fira%20Code&center=true&width=700&height=50&color=8B5CF6&vCenter=true&pause=3000&size=24&background=1A1B27&duration=4000" />
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

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=%F0%9F%9A%A7+Under+Development+-+Core+features+working!;More+improvements+coming+soon.&font=Fira%20Code&center=true&width=800&height=50&color=FFA500&vCenter=true&pause=1000000&size=16&duration=1&background=1A1B27" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=%F0%9F%94%AE+Coming+Soon:+Free+proxy+rotation;to+avoid+detection+without+paid+plans.&font=Fira%20Code&center=true&width=800&height=50&color=8B5CF6&vCenter=true&pause=1000000&size=16&duration=1&background=1A1B27" />
</p>

---

## 🎯 What is OPTX?

**OPTX** stands for **O**nline **P**rivacy **T**ool e**X**tractor — an Open Source Intelligence (OSINT) assistant designed to help you understand and manage your digital footprint.

> 💜 **My Mission:** Privacy is a fundamental right. OPTX gives you the tools to see what the internet knows about you and the path to removal — **completely for free**.

### What OPTX Does

| Feature | Description |
|---------|-------------|
| 🔍 **Phone Lookup** | Search 25+ people-search sites instantly *(more sites actively being added)* |
| 📊 **Carrier Info** | Live carrier & rate center data from public telecom records |
| 🤖 **AI Automation** | AI handles opt-out forms automatically, completely free |
| 🔐 **CAPTCHA Solver** | Audio CAPTCHA solving via Google Speech + wit.ai |
| 💬 **Chat Assistant** | OPTX Assistant guides you through the removal process |
| 🗺️ **Telecom Mapping** | Reverse-engineer phone number assignments across North America |
| 🛡️ **Privacy Advocacy** | Direct links to data broker opt-out pages |

---

## 🔒 Privacy

> [!NOTE]
> **API Mode**: Your chat messages are processed by OpenRouter's AI. Your personal data (name, address) for opt-outs stays local and is only used by the browser automation.
> 
> **Local Mode**: 100% private. Nothing leaves your machine.

- ✅ **Open source** — Audit the code yourself
- ✅ **Your control** — You decide what data to remove
- ✅ **No tracking** — No analytics or data collection

---

## 📋 Requirements

- **Python 3.11+**
- **Make** (see installation below if needed)

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

##  macOS

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
- **Auto:** AI does it automatically, completely free

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
├── index.html          # Main UI with glitch effects
├── style.css           # Cyberpunk-inspired styling
├── script.js           # Frontend logic & chat interface
├── sites.js            # 30+ data broker sites database
├── about.html          # About page
├── sources.html        # Data sources attribution
├── .env                # API keys (not committed)
├── Makefile            # Easy setup commands
└── backend/
    ├── agent.py        # 🧠 Main server - LLM, HyperAgent, CAPTCHA
    └── phone_lookup.py # Phone number info lookup
```

---

## 🎨 Website Theme

| Color | Hex | Usage |
|-------|-----|-------|
| ![Purple](https://img.shields.io/badge/-%238B5CF6-8B5CF6?style=flat-square) Purple | `#8B5CF6` | Primary accent, headings |
| ![Cyan](https://img.shields.io/badge/-%2301FFFF-01FFFF?style=flat-square) Cyan | `#01FFFF` | Links, highlights |
| ![Green](https://img.shields.io/badge/-%2300FF88-00FF88?style=flat-square) Green | `#00FF88` | Success states, buttons |
| ![Dark BG](https://img.shields.io/badge/-%231A1B27-1A1B27?style=flat-square) Dark | `#1A1B27` | Background |
| ![Card BG](https://img.shields.io/badge/-%230D1117-0D1117?style=flat-square) Darker | `#0D1117` | Cards, containers |

---

## 🔐 Environment Setup

Create `.env` in the project root:

```env
# Browserless (FREE CAPTCHA solving + residential proxies) - RECOMMENDED
# Get your key at: https://www.browserless.io
BROWSERLESS_API_KEY=your-key

# OR use Hyperbrowser (alternative browser automation)
# Get your key at: https://app.hyperbrowser.ai
HYPERBROWSER_API_KEY=hb_your-key

# LLM for Chat and Vision (get key from OpenRouter)
LLM_API_KEY=sk-or-v1-your-key

# Which model to use (pick any from OpenRouter, free options available)
LLM_MODEL=google/gemini-2.0-flash-exp:free

# CAPTCHA Solver backup (optional)
WIT_AI_SERVER_TOKEN=your-token
```

### 🔑 Getting Your API Keys

**1. OpenRouter (for AI Chat)**
- Go to [openrouter.ai/keys](https://openrouter.ai/keys)
- I recommend connecting with your GitHub account for easy signup
- Copy your API key and paste it as `LLM_API_KEY`

**2. Browserless (for CAPTCHA Solving + Proxies) - RECOMMENDED**
- Go to [browserless.io](https://www.browserless.io)
- Sign up for free (no credit card required)
- Copy your API key and paste it as `BROWSERLESS_API_KEY`
- **Free tier includes:** 1k units/month, auto CAPTCHA solving, residential proxies

**3. Hyperbrowser (Alternative Browser Automation)**
- Go to [app.hyperbrowser.ai](https://app.hyperbrowser.ai)
- Sign up and get your API key
- Alternative to Browserless if you prefer

**4. wit.ai (for Backup CAPTCHA Solving - Optional)**
- Follow this guide: [Configuring wit.ai](https://github.com/dessant/buster/wiki/Configuring-Wit.ai)
- Only needed as backup if Browserless CAPTCHA solving fails

### 🤖 About CAPTCHA Solving

**With Browserless (Recommended):** CAPTCHAs are solved automatically using their built-in solver.

**Without Browserless:** The free wit.ai solver works for many sites, but not all. Some CAPTCHAs may require manual solving.

**Coming Soon:** Additional CAPTCHA solver integrations:
- [Capsolver](https://docs.capsolver.com/en/pricing/)
- [2Captcha](https://2captcha.com/pricing)
- [NopeCHA](https://nopecha.com/pricing)

> [!NOTE]
> These services are NOT integrated yet, but will be added soon!

### 🌐 Browser Settings

Configure these in Settings > Browser Settings:

| Setting | Description | Default |
|---------|-------------|---------|
| **Stealth Mode** | Anti-detection & fingerprint randomization | ON |
| **Auto CAPTCHA** | Automatically solve CAPTCHAs | ON |
| **Residential Proxy** | Route through residential IPs (uses more units) | OFF |
| **Human-like Mode** | Smooth mouse & typing patterns | ON |
| **Adblock** | Block ads for faster page loads | ON |

### 🗑️ Account Deletion

If you want to delete your account from these services:

- **Browserless:** Email [support@browserless.io](mailto:support@browserless.io) with an account deletion request
- **Hyperbrowser:** Email [info@hyperbrowser.ai](mailto:info@hyperbrowser.ai) with an account deletion request (as stated in their [Privacy Policy](https://www.hyperbrowser.ai/privacy-policy))

> [!NOTE]
> I am NOT sponsored by Browserless or Hyperbrowser. For OPTX to work at its best, these are the best free options available.

---

## 📄 License

MIT License - Free to use, modify, and share!

---

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=Made%20by%20Khalid%20Khalel&font=Fira%20Code&center=true&width=300&height=30&color=8B5CF6&vCenter=true&pause=100000&size=18&duration=1" />
</p>
