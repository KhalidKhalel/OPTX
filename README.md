<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com/?lines=OPTX+-+Online+Privacy+Tool+eXtractor;Static+Frontend+OSINT+Assistant;Search+Public+People-Search+Sites;No+Backend+or+API+Keys;Made+by+Khalid+Khalel&font=Fira%20Code&center=true&width=700&height=50&color=8B5CF6&vCenter=true&pause=3000&size=24&background=1A1B27&duration=4000" />
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

# OPTX - Online Privacy Tool eXtractor

OPTX is a static OSINT assistant for opening public phone lookup and opt-out links across people-search and data broker sites.

<p align="center">
  <a href="https://optx-osint.netlify.app/" title="Live Website">
    <img src="https://img.shields.io/badge/%F0%9F%8C%90%20LIVE%20WEBSITE-OPTX%20OSINT-01FFFF?style=for-the-badge&labelColor=1A1B27" alt="Live Website"/>
  </a>
</p>

This version is frontend-only. It works with plain HTML, CSS, and JavaScript, has no backend, does not use API keys, and does not store searches in any OPTX database. Name, email, VIN, IP, and address lookup types are kept in the interface as coming-soon options.

## Features

| Feature | Description |
|:--|:--|
| Phone Search | Builds lookup links for US phone numbers. |
| Coming-soon types | Name, email, VIN, IP, and address are shown in the selector but disabled until those flows are ready. |
| Direct/manual modes | Shows whether a site can open a search URL directly or needs the user to search from the site form. |
| Site status | Attempts a browser-side reachability check for each site's homepage. |
| Free Scan | Links to free exposure-scan services and recommends using an alias email for signups. |
| Removal Guide | Explains the major broker networks to start with and links to high-value opt-out portals. |
| About | Explains OPTX, the people-search focus, and the static privacy model. |

## How It Works

1. Open `index.html` in a browser.
2. Keep the search type set to `Phone`.
3. Enter a 10-digit US phone number.
4. OPTX builds lookup links and opt-out links from `sites.js`.
5. The browser attempts a lightweight status check for each site's homepage.

The status dots only check whether a site appears reachable from the browser. They do not confirm whether a site has a match for your search. Some sites may show as `No response` or `Unconfirmed` if the site blocks browser-side probing, times out, or refuses a cross-origin request.

`sites.js` uses explicit `lookupTypes` for every entry. That keeps phone results limited to phone-capable sites while future name, email, VIN, IP, and address sources stay organized for later.

## Tabs

- `Search`: static lookup links, status indicators, and opt-out links.
- `Free Scan`: free exposure-scan providers with a static reflective panel.
- `Removal`: major broker-network guidance, important opt-out links, and alias/temp-mail suggestions.
- `About`: project overview and scope.

## Removal Order

Start with the largest broker networks first, then check the free scraping engines that often republish basic profiles.

1. `PeopleConnect, Inc.`: PeopleConnect, Intelius, Instant Checkmate, TruthFinder, and US Search.
2. `Inflection Risk Solutions`: BeenVerified, PeopleLooker, and NeighborWho.
3. `Independent powerhouses`: Whitepages, Spokeo, and PeopleFinders.
4. `Fast & free scraping engines`: TruePeopleSearch, FastPeopleSearch, and Radaris.

For opt-out forms or free scan signups, use a separate temporary inbox when possible:

- [Temp Mail](https://temp-mail.org/)
- [Tmailor](https://tmailor.com/)
- [NukeMail](https://nukemail.app/)
- [TempMail.co](https://www.tempmail.co/)
- [MailTicking](https://www.mailticking.com/)

## Project Structure

```text
OPTX/
├── assets/
│   ├── favicon.ico
│   └── logo.png
├── index.html
├── script.js
├── sites.js
├── style.css
├── netlify.toml
└── README.md
```

## Development

No install step is required. The app is plain HTML, CSS, and JavaScript, designed to deploy directly as a static Netlify site.

## Deploying on Netlify

This project is ready to deploy as a static site on Netlify.

Use these settings:

```text
Build command: leave blank
Publish directory: .
```

The included `netlify.toml` sets the publish directory and a few safe static-site headers. Because the project is static, Netlify does not need Python, a server, functions, environment variables, or build tooling.

## Scope

OPTX focuses on public lookup and opt-out links for privacy education and personal digital-footprint review. It does not target employment screening, tenant screening, credit reporting, or other regulated background-check services.

## License

MIT License - free to use, modify, and share.
