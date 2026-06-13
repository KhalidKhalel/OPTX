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

OPTX is a static OSINT assistant for opening public phone lookup, reverse image search, and opt-out links across people-search and data broker sites.

<p align="center">
  <a href="https://optx-osint.netlify.app/" title="Live Website">
    <img src="https://img.shields.io/badge/%F0%9F%8C%90%20LIVE%20WEBSITE-OPTX%20OSINT-01FFFF?style=for-the-badge&labelColor=1A1B27" alt="Live Website"/>
  </a>
</p>

This version is mostly frontend-only. It works with plain HTML, CSS, JavaScript, and one Netlify Function that uploads reverse-image files to Litterbox for a temporary public URL. If the function is unavailable while testing locally, OPTX falls back to a direct Litterbox browser upload. It does not use API keys and does not store searches in any OPTX database. Name, email, VIN, IP, and address lookup types are kept in the interface as coming-soon options.

## Features

| Feature | Description |
|:--|:--|
| Phone Search | Builds lookup links for US phone numbers. |
| Reverse Image Search | Uploads an image to a temporary Litterbox URL and opens reverse image search tools. |
| Coming-soon types | Name, email, VIN, IP, and address are shown in the selector but disabled until those flows are ready. |
| Direct/manual modes | Shows whether a site can open a search URL directly or needs the user to search from the site form. |
| Site status | Attempts a browser-side reachability check for each site's homepage. |
| Free Scan | Links to free exposure-scan services, OSINT resource directories, and alias-email tools. |
| Removal Guide | Explains major broker networks, map imagery blur requests, and high-value privacy resources. |
| About | Explains OPTX, the people-search focus, and the static privacy model. |

## How It Works

### Phone Search

1. Open the live Netlify site.
2. Keep the search type set to `Phone`.
3. Enter a 10-digit US phone number.
4. OPTX builds lookup links and opt-out links from `sites.js`.
5. The browser attempts a lightweight status check for each site's homepage.

The status dots only check whether a site appears reachable from the browser. They do not confirm whether a site has a match for your search. Some sites may show as `No response` or `Unconfirmed` if the site blocks browser-side probing, times out, or refuses a cross-origin request.

`sites.js` uses explicit `lookupTypes` for every entry. That keeps phone results limited to phone-capable sites while future name, email, VIN, IP, address, username, wallet, and plate sources stay organized for later. Current future-source entries include tools such as Lullar, EmailSherlock, Mailmeteor, OpenPayrolls, and IntelTechniques.

### Reverse Image Search

1. Open the `Search` tab.
2. Set `Search type` to `Image`.
3. Upload an image and choose a Litterbox expiration: `1h`, `12h`, `24h`, or `72h`.
4. The Netlify Function uploads it to Litterbox and returns a temporary public image URL. Local testing can fall back to direct Litterbox upload if the function endpoint is not available.
5. OPTX builds `Free Sites` and `Paid Sites` tables for TinEye, Google Lens, Bing, Yandex, Copyseeker, Searqle, image-geolocation tools, and other reverse image tools.
6. Use `Lookup` to open a reverse image search and `Opt-out` or `Info` for removal guidance. `D` means direct lookup and `M` means manual lookup.
7. Use `Copy URL` for tools that require manual upload or paste.

Do not upload private or sensitive images. The image URL is temporary, but it is public while active. Anonymous Litterbox uploads expire automatically; Litterbox does not expose an anonymous early-delete endpoint. Catbox file deletion exists for userhash/account uploads, which OPTX intentionally does not use. Some image search tools cannot remove source images directly; remove the image from the original host first, then use the search engine's removal or refresh process if needed.

## Tabs

- `Search`: phone lookup, reverse image search, status indicators, and opt-out links from the `Search type` dropdown.
- `Free Scan`: free exposure-scan providers, IntelTechniques tools, OSINT Framework, and temp-mail recommendations.
- `Removal`: major broker-network guidance, map imagery blur request help, important opt-out links, and alias/temp-mail suggestions.
- `About`: project overview and scope.

The footer links back to [KhalidKhalel.com](https://www.khalidkhalel.com/) as the project portfolio credit.

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
- [AdGuard Temp Mail](https://adguard.com/en/adguard-temp-mail/overview.html)

The Removal tab also includes:

- Google Maps Street View blur steps with a walkthrough link.
- Apple Maps Look Around email template generation for `MapsImageCollection@apple.com`.
- The official [National Do Not Call Registry](https://donotcall.gov/) as a phone-privacy resource.

## Project Structure

```text
OPTX/
├── assets/
│   ├── favicon.ico
│   └── logo.png
├── netlify/
│   └── functions/
│       └── upload-image.js
├── index.html
├── script.js
├── sites.js
├── style.css
├── netlify.toml
└── README.md
```

## Development

No install step is required. The app is plain HTML, CSS, JavaScript, and one Netlify Function, designed to deploy directly on Netlify.

## Deploying on Netlify

This project is ready to deploy as a static site on Netlify.

Use these settings:

```text
Build command: leave blank
Publish directory: .
```

The included `netlify.toml` sets the publish directory, function directory, and a few safe static-site headers. Netlify does not need Python, environment variables, or build tooling for this project.

## Scope

OPTX focuses on public lookup and opt-out links for privacy education and personal digital-footprint review. It does not target employment screening, tenant screening, credit reporting, or other regulated background-check services.

## License

MIT License - free to use, modify, and share.
