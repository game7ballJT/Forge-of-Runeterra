# Forge of Runeterra — Deployment Guide
## Complete step-by-step instructions for GitHub Pages

This guide assumes you have never deployed a website before.
Follow each step in order. It takes about 15 minutes the first time.

---

## What you are deploying

The `site/` folder contains everything. The structure is:

```
site/
  index.html          ← Your main interactive app (unchanged)
  sitemap.xml         ← Tells Google/AI crawlers about all your pages
  robots.txt          ← Tells AI crawlers they can read everything
  champions/
    ahri/index.html   ← Crawlable Ahri page at /champions/ahri/
    jinx/index.html   ← Crawlable Jinx page at /champions/jinx/
    ... (166 champion pages total)
  counters/
    ahri-vs-yasuo/    ← Matchup page at /counters/ahri-vs-yasuo/
    ... (498 matchup pages)
  guides/
    best-adc-patch-26-13/   ← Meta guide at /guides/best-adc-patch-26-13/
    ... (5 role guides)
  patch/
    26-13/index.html  ← Patch notes at /patch/26-13/
```

---

## Step 1 — Create a GitHub account (skip if you already have one)

1. Go to **https://github.com**
2. Click **Sign up**
3. Enter your email, create a password, choose a username
4. Verify your email address

---

## Step 2 — Create a new repository

1. After logging in, click the **+** button in the top right corner
2. Click **New repository**
3. For **Repository name**, type exactly: `forgeofruneterra.gg`
   (If you already have a repo, you can use that one — skip to Step 4)
4. Make sure **Public** is selected (GitHub Pages requires this on free plans)
5. Do NOT check "Add a README file" or anything else
6. Click **Create repository**

---

## Step 3 — Upload all the files

You have two options. Option A is easier. Option B is recommended for future patches.

### Option A — Drag and drop (easiest, no software needed)

1. On the new empty repository page, look for the text that says
   **"uploading an existing file"** — click that link
2. Open the `site/` folder on your computer
3. Select ALL files and folders inside it (Ctrl+A on Windows, Cmd+A on Mac)
4. Drag them ALL into the GitHub upload window
5. Wait for all files to upload (this will take a few minutes — 675 files)
6. At the bottom of the page, click **Commit changes**

### Option B — GitHub Desktop (recommended for future patch updates)

1. Download **GitHub Desktop** from https://desktop.github.com/
2. Install it and log in with your GitHub account
3. Click **Clone a repository from the Internet**
4. Select your `forgeofruneterra.gg` repository
5. Choose where to save it on your computer, click **Clone**
6. Copy the CONTENTS of the `site/` folder into the cloned folder
7. In GitHub Desktop, you'll see all the files listed as changes
8. Type "Initial deploy" in the Summary box, click **Commit to main**
9. Click **Push origin**

---

## Step 4 — Enable GitHub Pages

1. On your repository page on GitHub, click **Settings** (tab at the top)
2. In the left sidebar, scroll down and click **Pages**
3. Under **Source**, select **Deploy from a branch**
4. Under **Branch**, select **main** and **/ (root)**
5. Click **Save**
6. Wait 1–2 minutes, then refresh the page
7. You should see a green box saying
   **"Your site is live at https://[your-username].github.io/forgeofruneterra.gg/"**

At this point your site is live at a `github.io` URL, but not yet at `forgeofruneterra.gg`.

---

## Step 5 — Connect your custom domain (forgeofruneterra.gg)

### Add the CNAME file to your repository

1. On your repository page, click **Add file → Create new file**
2. Name the file exactly: `CNAME`
3. In the file content, type just your domain on one line:
   ```
   forgeofruneterra.gg
   ```
4. Click **Commit new file**

### Update your DNS settings at your domain registrar

Your domain registrar is wherever you bought forgeofruneterra.gg
(Namecheap, GoDaddy, Google Domains, Cloudflare, etc.).

Log in to your registrar and find the **DNS settings** or **DNS management** panel.

Add these records:

| Type  | Host/Name       | Value/Points to       |
|-------|-----------------|----------------------|
| A     | @               | 185.199.108.153       |
| A     | @               | 185.199.109.153       |
| A     | @               | 185.199.110.153       |
| A     | @               | 185.199.111.153       |
| CNAME | www             | [your-username].github.io |

These are GitHub's actual IP addresses. They don't change.

DNS changes take 10 minutes to 48 hours to propagate globally.
Most are visible within 1 hour.

### Finish in GitHub Settings

1. Go back to your repository **Settings → Pages**
2. In the **Custom domain** box, type: `forgeofruneterra.gg`
3. Click **Save**
4. Check **Enforce HTTPS** once the option becomes available
   (this may take a few minutes after DNS propagates)

---

## Step 6 — Verify it works

Open your browser and go to:
- `https://forgeofruneterra.gg/` — your main app (should look identical to before)
- `https://forgeofruneterra.gg/champions/ahri/` — Ahri's crawlable page
- `https://forgeofruneterra.gg/patch/26-13/` — the Patch 26.13 breakdown
- `https://forgeofruneterra.gg/sitemap.xml` — list of all pages

If the main app works but champion pages show a 404, wait 5 minutes and try again.
GitHub Pages sometimes takes a few minutes to register all the new paths.

---

## Step 7 — Submit to Google Search Console (important for GEO)

This tells Google your site exists and to crawl it immediately.

1. Go to **https://search.google.com/search-console**
2. Click **Add property** → **URL prefix** → enter `https://forgeofruneterra.gg/`
3. Verify ownership (easiest method: choose **HTML file** upload and follow instructions)
4. Once verified, click **Sitemaps** in the left sidebar
5. Enter `sitemap.xml` and click **Submit**

Google will now discover all 673 pages and begin indexing them.
Expect them to appear in search results within 1–4 weeks.

---

## How to update for the next patch (Patch 26.14)

When the next patch drops:

1. Open `generate_site.py` in any text editor
2. Find the line `PATCH = '26.13'` and change it to `'26.14'`
3. Find `PATCH_DATE` and update the date
4. Update the `PATCH_DATA` dictionary with the new buffs/nerfs
5. Run: `python3 generate_site.py`
6. Replace the old `site/` folder contents with the new ones
7. Push to GitHub (either drag-and-drop upload or via GitHub Desktop)

The generator script is yours — it lives in `generate_site.py` and
can rebuild the entire 674-file site in under 60 seconds.

---

## Troubleshooting

**"404 Not Found" on champion pages**
→ Wait 5 minutes after upload. GitHub Pages takes time to register all paths.
→ Make sure you uploaded the contents of `site/`, not the `site/` folder itself.

**Custom domain not working**
→ DNS propagation can take up to 48 hours. Test with `https://[username].github.io/forgeofruneterra.gg/champions/ahri/` first.
→ Make sure the CNAME file contains only the domain name, no extra characters.

**"Your connection is not private" warning**
→ HTTPS isn't provisioned yet. Wait 10–15 minutes after DNS propagates, then check the "Enforce HTTPS" checkbox in Settings → Pages.

**Main app looks different than before**
→ The `site/index.html` IS your original file — it's identical to what you had, just with two small additions: a hidden link inside each champion card and a few `<link>` tags in the head. No visual change.
