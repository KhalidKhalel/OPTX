<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com/?lines=OPTX+-+Online+Privacy+Tool+eXtractor;Protect+Your+Privacy+Online;Know+Where+Your+Data+Lives;Remove+Your+Digital+Footprint;Learn+to+Limit+Your+Online+Exposure;Made+by+Khalid+Khalel&font=Fira%20Code&center=true&width=700&height=50&color=8B5CF6&vCenter=true&pause=3000&size=24&background=1A1B27&duration=4000" />
  </a>
</p>

<p align="center">
  <a href="https://www.khalidkhalel.com/" title="Website"><img width="32px" alt="Website" src="https://img.icons8.com/ios/50/8B5CF6/internet.png"/></a>
  &#8287;&#8287;&#8287;&#8287;&#8287;
  <a href="https://linkedin.com/in/khalidkhalel" title="LinkedIn"><img width="32px" alt="LinkedIn" src="https://img.icons8.com/ios/50/8B5CF6/linkedin.png"/></a>
  &#8287;&#8287;&#8287;&#8287;&#8287;
  <a href="mailto:contact.khalidk@gmail.com" title="Email"><img width="32px" alt="Email" src="https://img.icons8.com/ios/50/8B5CF6/mail.png"/></a>
</p>

---

> [!WARNING]
> **Early Beta** — The automated removal process is in active development. It currently supports one site for testing purposes with more being added soon.

## What is OPTX?

**OPTX** (Online Privacy Tool eXtractor) is an Open Source Intelligence (OSINT) assistant designed to help users understand and manage their digital footprint. By providing transparent access to public telecom and data broker information, users can see exactly what information is publicly available about them.

### People Search Sites

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
| **Phone Lookup** | Search **100+** people-search sites instantly |
| **Dual-Table View** | Side-by-side comparison of **Free** and **Paid** data sources |
| **Automated Removal** | Cloud browser fills opt-out forms and confirms verification emails automatically |
| **Live Preview** | Watch the automation navigate forms in real-time in the browser |
| **CAPTCHA Solving** | Native integration with Browserless stealth and captcha solving |
| **Smart Playbooks** | Pre-defined step-by-step removal flows for each data broker site |
| **Temp Email** | Guerrilla Mail generates disposable inboxes for verification emails |

---

## How It Works

### 1. Search
Enter a phone number → OPTX checks **100+** data broker sites (new ones added daily).

### 2. Review
See which sites have your info with direct links to their opt-out forms.

### 3. Removal Process
Head to the **Removal** section, input your information (Name, Address, etc.) and click **Start Removal**.

Each data broker has its own playbook — a set of step-by-step instructions that tell the automation exactly what to do on that site. Some sites require email verification, so those playbooks use a two-session approach:

1. **Session 1** — Connects a cloud browser, navigates to the opt-out page, fills the form, solves CAPTCHAs, and submits
2. **Email Verification** — Polls a temporary Guerrilla Mail inbox for the verification email
3. **Session 2** — Opens a fresh browser session to click the verification link and confirm removal

Other sites that don't require email verification are handled in a single session. Each session uses residential proxy rotation and stealth mode to avoid detection.

---

## How OPTX Compares

| Feature | **OPTX** | **Privotron** | **DataBroker Remover** | **JustVanish** | **DataBrokerBreaker** | **PrivacyBot** | **BADBOOL** |
|---------|----------|---------------|------------------------|----------------|-----------------------|----------------|-------------|
| **Approach** | Browser automation | Browser automation | Email requests | Email requests | Browser automation | Email requests | Manual guide |
| **Sites Covered** | 100+ searched, growing playbooks | Community-contributed | 60+ brokers | 100+ brokers | 7 sites | Large list | 100+ listed |
| **CAPTCHA Solving** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A |
| **Stealth / Anti-Detection** | ✅ Residential proxies + stealth | ❌ Local browser | ❌ | ❌ | ❌ VPN recommended | ❌ | N/A |
| **Live Browser Preview** | ✅ Real-time WebSocket feed | ❌ | ❌ | ❌ | ❌ | ❌ | N/A |
| **Temp Email Verification** | ✅ Guerrilla Mail built-in | ❌ | ❌ | ❌ Uses your real email | ⚠️ Warns temp email is too slow | ❌ Uses your Gmail | N/A |
| **Web UI** | ✅ Full SPA | ❌ CLI only | ✅ Web app | ❌ CLI only | ❌ CLI only | ✅ Local web UI | ❌ GitHub page |
| **Requires AWS / Cloud Setup** | ❌ | ❌ | ✅ AWS SES + DynamoDB | ❌ | ❌ | ❌ | N/A |
| **Fully Automated** | ✅ | ⚠️ Some prompts | ✅ | ⚠️ Not production-ready | ❌ Requires user interaction | ✅ | ❌ Manual |
| **Phone Number Search** | ✅ 100+ sites | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Cost** | Free (Browserless free tier) | Free | Free (AWS costs apply) | Free | Free | Free | Free |
| **Language** | Python | Python | TypeScript | Go | Python | Python | N/A |
| **GitHub** | You're here | [kevinl95/Privotron](https://github.com/kevinl95/Privotron) | [visible-cx/databroker_remover](https://github.com/visible-cx/databroker_remover) | [AnalogJ/justvanish](https://github.com/AnalogJ/justvanish) | [Awesome-Austin/DataBrokerBreaker](https://github.com/Awesome-Austin/DataBrokerBreaker) | [privacybot-berkeley/privacybot](https://github.com/privacybot-berkeley/privacybot) | [yaelwrites/Big-Ass-Data-Broker-Opt-Out-List](https://github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List) |

> [!NOTE]
> **BADBOOL** (Big-Ass Data Broker Opt-Out List) is not a tool — it's a comprehensive manual reference list of data broker opt-out links maintained by the community. Many automation tools (including OPTX) use it as a knowledge base.

---

## Installation

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

### macOS

**Option 1: Xcode Command Line Tools** (Recommended)

```bash
xcode-select --install
```

A popup will appear - click "Install" and wait for it to complete.

**Option 2: Using Homebrew**

```bash
brew install make
```

### Windows

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

### Verify Make Installation

```bash
make --version
```

---

## Built With

| Technology | Purpose | Icon |
|------------|---------|------|
| **Python** | Backend server and browser automation | <a href="https://www.python.org"><img src="https://skillicons.dev/icons?i=python&theme=dark" width="30"/></a> |
| **JavaScript** | Frontend logic and dynamic UI | <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://skillicons.dev/icons?i=js&theme=dark" width="30"/></a> |
| **HTML5** | Page structure and semantic markup | <a href="https://www.w3.org/html/"><img src="https://skillicons.dev/icons?i=html&theme=dark" width="30"/></a> |
| **CSS3** | Premium cyberpunk styling and animations | <a href="https://www.w3schools.com/css/"><img src="https://skillicons.dev/icons?i=css&theme=dark" width="30"/></a> |
| **FastAPI** | REST API endpoints and WebSocket server | <a href="https://fastapi.tiangolo.com"><img src="https://skillicons.dev/icons?i=fastapi&theme=dark" width="30"/></a> |

---

## Project Structure

```
OPTX/
├── assets/             # Branding and documentation assets
│   ├── logo.png
│   └── README.md       # Backup documentation
├── index.html          # Main SPA - all views (search, removal, about)
├── style.css           # Organized CSS with dedicated comments
├── script.js           # Frontend logic, WebSocket, and UI management
├── sites.js            # Database of 100+ data broker sites
├── .env                # API keys (gitignored)
├── Makefile            # Easy commands: make, update, clean
└── backend/
    ├── agent.py         # Core server: browser automation, email service, WebSocket
    ├── playbooks.py     # Step-by-step removal flows for each data broker site
    └── requirements.txt # Project dependencies
```

---

## Environment Setup

Create `.env` in the project root:

```env
# Browser Automation - Browserless
# Get your key at: https://browserless.io
BROWSERLESS_API_KEY=your-key
```

### Getting Your API Key

**Browserless — FREE Tier**

Sign up at [browserless.io](https://www.browserless.io) — the free tier includes:

| What You Get | Details |
|--------------|---------|
| **1,000 units / month** | 1 unit = 30 seconds of browser time |
| **CAPTCHA solving** | Built-in, no extra config needed |
| **Residential proxies** | Charged at 6 units per MB |
| **Stealth mode** | `/stealth` route hides all signs of automation |
| **3 global regions** | San Francisco, London, Amsterdam |
| **Chrome, Firefox, WebKit** | All major browsers available |
| **1 concurrent session** | Max 1 browser running at a time |
| **1-minute max session** | Sessions auto-close after 60 seconds |

> [!TIP]
> 1,000 free units is roughly **8+ hours** of browser time per month — more than enough for personal use.

### Account Deletion (Your Rights)

If you wish to close your accounts and delete your data from the services used by OPTX, you can do so by contacting their respective support teams as per their privacy policies:

*   **Browserless (The Browser)**: Email `support@browserless.io` to request account closure and data deletion. [Privacy Policy](https://www.browserless.io/privacy-policy)

---

## License

MIT License - Free to use, modify, and share!

---

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=Made%20by%20Khalid%20Khalel&font=Fira%20Code&center=true&width=300&height=30&color=8B5CF6&vCenter=true&pause=100000&size=18&duration=1" />
</p>
