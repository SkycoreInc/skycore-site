# SkyCore Solutions — Website

A rebuilt static marketing site for SkyCore Solutions. Modern, responsive, dark-themed, with a self-maintaining blog.

## What's here

```
site/
├── index.html              Homepage (hero, services, process, stats, proof, blog preview, CTA)
├── services.html           Full services page with 5 service sections
├── about.html              Story, values, team, stats
├── contact.html            Contact form + office info
├── blog/
│   ├── index.html          Blog listing (auto-populates from posts.js)
│   ├── posts.js            Blog manifest — source of truth for listings
│   ├── GENERATOR_PROMPT.md The prompt the scheduled agent runs every 2 days
│   ├── the-50000-dollar-sentence.html     (2026-04-09)
│   ├── microsoft-365-backup-myth.html     (2026-04-11)
│   ├── cloud-bill-doubled.html            (2026-04-13)
│   └── 4-minute-phishing-test.html        (2026-04-15)
├── assets/
│   ├── css/style.css       All styles (single file, ~600 lines)
│   └── js/main.js          Nav, mobile menu, reveal animations, form stub
└── scripts/
    ├── publish-blog.ps1    Local fallback: runs Claude to publish one post
    └── install-task.ps1    One-time: registers Windows scheduled task (every 2 days @ 9am)
```

No build step. No dependencies. Open `index.html` in a browser and it runs.

## Preview locally

Any static server works:

```bash
# Python
python -m http.server 8000

# Node
npx serve .
```

Then visit `http://localhost:8000`.

## Deploy

Pick one — all work without changes:

| Host | How |
|---|---|
| **Netlify** | Drag the `site/` folder onto app.netlify.com/drop |
| **Vercel** | `vercel` in the `site/` dir |
| **Cloudflare Pages** | Push to GitHub, connect in Cloudflare dashboard |
| **GitHub Pages** | Push `site/` contents to a repo, enable Pages |
| **S3 + CloudFront** | `aws s3 sync site/ s3://your-bucket --delete` |
| **Traditional web host** | FTP the `site/` contents to the web root |

Point the `skycoresolutions.com` domain at whichever host you pick.

## The auto-publishing blog — every 2 days

A new, short blog post is published automatically every 2 days. Two ways to run it:

### Option A — Scheduled remote agent (preferred, no machine required)

Creates a cloud-hosted scheduled Claude agent that runs independently of your laptop.

1. In Claude Code, run `/schedule` — it'll walk you through creating a task.
2. Schedule name: `skycore-blog-every-2-days`
3. Cadence: every 2 days at 09:00 UTC
4. Prompt: paste the contents of `site/blog/GENERATOR_PROMPT.md`

**Note:** if `/schedule` returns a connection error, retry in a few minutes. It talks to your claude.ai account to register the task.

### Option B — Local Windows Task Scheduler (fallback)

Runs the publisher on this machine every 2 days. Requires the `claude` CLI on PATH.

```powershell
# One-time, from an elevated (admin) PowerShell:
cd "C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site\scripts"
.\install-task.ps1
```

What it does:
- Registers a Windows task named `SkyCore-Blog-Every-2-Days`
- Runs `publish-blog.ps1` every 2 days at 9:00 AM
- Logs output to `site/scripts/publish.log`
- The task will wake the machine if asleep and run on next boot if missed

Verify:
```powershell
Get-ScheduledTask -TaskName SkyCore-Blog-Every-2-Days
# Manually trigger a test run:
Start-ScheduledTask -TaskName SkyCore-Blog-Every-2-Days
```

Uninstall:
```powershell
Unregister-ScheduledTask -TaskName SkyCore-Blog-Every-2-Days -Confirm:$false
```

## Publishing a post by hand

You can also just run the generator prompt once, ad hoc:

```bash
cd "C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site"
claude --print --permission-mode acceptEdits "$(cat blog/GENERATOR_PROMPT.md)"
```

It'll create a new HTML file and update `posts.js`.

## How the blog renders without a backend

`blog/posts.js` exposes `window.SKYCORE_POSTS` — a simple JS array. Three places read it:

1. **Homepage** (`index.html`) — shows the 3 newest posts in the "Latest from the blog" section.
2. **Blog index** (`blog/index.html`) — shows all posts, newest first.
3. **Individual post pages** — hand-written HTML, no dependency on the manifest.

So when a new post is added:
- A new HTML file is created in `blog/`
- A new entry is prepended to `SKYCORE_POSTS`
- The homepage and blog index pick it up automatically on next load

This is why there's no build step. The site works from `file://` or any static host.

## Customizing

| What | Where |
|---|---|
| Colors, fonts, spacing | `assets/css/style.css` — all CSS variables at the top |
| Navigation links | Every HTML file — search for `<nav class="nav-links">` |
| Services content | `services.html` |
| Contact form backend | `assets/js/main.js` — wire the `#contact-form` submit to Formspree, Basin, or your own endpoint |
| Phone / email / address | Footer of each HTML file + `contact.html` |
| Company stats | `index.html` and `about.html` — `.stats` section |

## Contact form wiring (30 seconds)

The form currently shows a success message without actually sending. To wire to Formspree:

1. Sign up at formspree.io, create a form, copy the endpoint URL.
2. In `contact.html`, change `<form id="contact-form" class="form">` to:
   `<form id="contact-form" class="form" action="https://formspree.io/f/YOUR_ID" method="POST">`
3. In `assets/js/main.js`, remove the submit handler so the form submits natively.

## Credits

Built on vanilla HTML/CSS/JS. Zero frameworks, zero build tools. Inter via Google Fonts.
