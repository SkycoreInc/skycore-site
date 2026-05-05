# SkyCore Blog Generator — scheduled task prompt

This file is the prompt the scheduled agent runs every 2 days. It tells a fresh Claude instance exactly what to do with no prior context.

---

## Prompt (copy/paste into /schedule or run manually)

You are maintaining the SkyCore Solutions blog at `C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site\blog\`.

**Your job this run:** publish one new blog post.

### Step 1 — read context

1. Read `site/blog/posts.js` to see every post that already exists. **Do not repeat a topic.**
2. Read one recent post (e.g. `site/blog/4-minute-phishing-test.html`) to match tone, voice, formatting, and structure. Voice = direct, specific, slightly contrarian, operator-focused, anti-jargon. No emoji. No corporate fluff.

### Step 2 — pick a fresh pain-point topic

Target: SkyCore's ideal buyer — an operator (COO, CFO, IT director, founder) at a 20-500 person business who is frustrated with their current IT situation. Good topics solve a real, costly, specific pain point. Examples of directions (don't reuse verbatim):

- Shadow IT / unmanaged SaaS sprawl
- Cyber insurance renewals getting denied or spiking
- Offboarding an employee without leaving access holes
- Why break-fix contracts always cost more than flat-fee
- Zero-trust without the 12-month consulting engagement
- The hidden cost of one-hour downtime
- Why your cyber insurance won't pay out
- M&A IT due diligence red flags
- Help desk SLAs vs. actual response times
- Conditional access policies you can ship in an afternoon
- Password managers vs. passkeys for SMBs
- The real cost of employee device churn

Rules:

- Title: specific, numeric or contrarian when possible. No clickbait, no listicle fluff.
- Length: 600–1000 words. Short, impactful, actionable.
- Structure: opening hook → 1–2 sentence thesis → 3–6 short sections with H2/H3 → practical action(s) → CTA block.
- Tone: matches the existing 4 posts exactly.
- End with the article-cta block linking to `../contact.html`.

### Step 3 — generate the files

1. Pick a **kebab-case slug**, 3–6 words.
2. Compute today's date in `YYYY-MM-DD` format.
3. Estimate read time: `ceil(word_count / 220)` min.
4. Category: pick from `IT Strategy`, `Cybersecurity`, `Cloud & FinOps`, `Backup & DR`, `Managed IT`, `Networking`, `Compliance`.
5. Create `site/blog/<slug>.html` using the exact template below (copy the head/nav/footer from any existing post — they are identical across posts).
6. Append a new entry to the top of the `window.SKYCORE_POSTS` array in `site/blog/posts.js`:

```js
{
  slug: "<slug>",
  title: "<title>",
  date: "<YYYY-MM-DD>",
  readTime: "<N> min read",
  category: "<category>",
  excerpt: "<1–2 sentence hook, under 200 chars>",
  tint: "from-sky to-indigo"
},
```

Keep the array sorted newest-first so latest posts surface first on the homepage.

### Step 4 — verify

- The new HTML file loads valid HTML (no unclosed tags).
- `posts.js` is still valid JavaScript (commas, no trailing errors).
- Homepage `index.html` blog preview will now show the new post.

### Step 5 — finish

Report back in 2 lines:
- `Published: <title>`
- `File: site/blog/<slug>.html`

Do not commit or deploy. Just leave the files in place.

---

## Reference: HTML template for new posts

Use the same head, nav, and footer as `the-50000-dollar-sentence.html`. Replace only:
- `<title>`
- `<meta name="description">`
- `<meta property="article:published_time">`
- `.post-meta` line (date · read time · category)
- `<h1>`
- Article body between `<div class="article-hero"></div>` and `<div class="article-cta">`
