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
| 🔍 **Phone Lookup** | Search **100+** people-search sites instantly |
| 📊 **Dual-Table View** | Side-by-side comparison of **Free** and **Paid** data sources |
| 🛡️ **Removal Form** | Streamlined, premium UI with auto-filling rows for quick data entry |
| 📺 **Live Preview** | Watch the automation navigate forms in real-time in the browser |
| 🔐 **CAPTCHA Solving** | Native integration with Browserless and optional Wit.ai audio solving |
| 🏗️ **Smart Playbooks** | Pre-defined removal flows for accurate form submission |

---

## 🎮 How It Works

### 1️⃣ Search
Enter a phone number → OPTX checks **100+** data broker sites (new ones added daily).

### 2️⃣ Review
See which sites have your info with direct links to their opt-out forms.

### 3️⃣ Removal Process
If you head over to the **Removal** section, you can input your information (Name, Address, etc.) into the form and click **Start Removal**. 

This information is used to **automatically fill out removal forms on your behalf**. The system connects to a cloud browser, navigates to each site's opt-out page, and injects your details into the necessary fields—saving you hours of manual typing and navigating through confusing opt-out loops.

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

### 🍎 macOS

**Option 1: Xcode Command Line Tools** (Recommended)

```bash
xcode-select --install
```

A popup will appear - click "Install" and wait for it to complete.

**Option 2: Using Homebrew**

```bash
brew install make
```

### ⊞ Windows

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

### ✅ Verify Make Installation

```bash
make --version
```

---

## 🛠️ Built With

| Technology | Purpose | Icon |
|------------|---------|------|
| **Python** | Backend server and browser automation | <a href="https://www.python.org"><img src="https://skillicons.dev/icons?i=python&theme=dark" width="30"/></a> |
| **JavaScript** | Frontend logic and dynamic UI | <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://skillicons.dev/icons?i=js&theme=dark" width="30"/></a> |
| **HTML5** | Page structure and semantic markup | <a href="https://www.w3.org/html/"><img src="https://skillicons.dev/icons?i=html&theme=dark" width="30"/></a> |
| **CSS3** | Premium cyberpunk styling and animations | <a href="https://www.w3schools.com/css/"><img src="https://skillicons.dev/icons?i=css&theme=dark" width="30"/></a> |
| **FastAPI** | REST API endpoints and WebSocket server | <a href="https://fastapi.tiangolo.com"><img src="https://skillicons.dev/icons?i=fastapi&theme=dark" width="30"/></a> |

---

## 📁 Project Structure

```
OPTX/
├── assets/             # Branding and documentation assets
│   ├── logo.png
│   └── README.md       # Backup documentation
├── index.html          # Main SPA - all views (search, removal, about)
├── style.css           # Highly organized CSS with dedicated comments
├── script.js           # Frontend logic and UI management
├── sites.js            # Database of 100+ data broker sites
├── .env                # Your API keys (not committed to git)
├── Makefile            # Easy commands: make, update, clean
└── backend/
    ├── agent.py         # Core server using Browserless for automation
    ├── playbooks.py     # Defined steps for individual site removals
    └── requirements.txt # Project dependencies
```

---

## 🔐 Environment Setup

Create `.env` in the project root:

```env
# Browser Automation - Browserless (FREE Tier available)
# Get your key at: https://browserless.io
BROWSERLESS_API_KEY=your-key

# CAPTCHA Solver (Audio) - Optional but useful for complex bots
WIT_AI_SERVER_TOKEN=your-token
```

### 🔑 Getting Your API Keys

**1. Browserless (The Browser) - FREE Tier**
- Full-featured cloud browser with anti-detection and CAPTCHA solving.
- Sign up at [browserless.io](https://www.browserless.io).
- **Stealth & CAPTCHA**: Provides comprehensive handling through both passive detection and programmatic solving. Many CAPTCHAs are prevented altogether by using the `/stealth` route, which hides signs of automation using advanced anti-detection techniques.

**2. CAPTCHA Solver (Audio) - 100% FREE**
- Optional but recommended for audio-based reCAPTCHA solving.
- [Wit.ai](https://wit.ai) | [GitHub](https://github.com/dessant/buster) | [Buster Config Guide](https://github.com/dessant/buster/wiki/Configuring-Buster-for-Wit.ai)

### 🗑️ Account Deletion (Your Rights)

If you wish to close your accounts and delete your data from the services used by OPTX, you can do so by contacting their respective support teams as per their privacy policies:

*   **Browserless (The Browser)**: Email `support@browserless.io` to request account closure and data deletion. [Privacy Policy](https://www.browserless.io/privacy-policy)

> [!TIP]
> **Why is it free?** OPTX leverages the generous free tiers of best-in-class privacy infrastructure. You get professional-grade removal tools without a monthly subscription.

---

## 📄 License

MIT License - Free to use, modify, and share!

---

<p align="center">
  <img src="https://readme-typing-svg.demolab.com/?lines=Made%20by%20Khalid%20Khalel&font=Fira%20Code&center=true&width=300&height=30&color=8B5CF6&vCenter=true&pause=100000&size=18&duration=1" />
</p>
